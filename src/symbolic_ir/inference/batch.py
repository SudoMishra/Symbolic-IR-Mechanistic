"""Provider batch submission and result recovery for OpenAI and Anthropic."""

from __future__ import annotations

import copy
import hashlib
import json
import os
import tempfile
import time
from pathlib import Path
from typing import Any, Iterator

from symbolic_ir.budget import calculate_cost


def _load_env_key(key_name: str) -> str | None:
    val = os.environ.get(key_name)
    if not val:
        env_file = Path(".env")
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    if k.strip() == key_name:
                        val = v.strip()
                        os.environ[key_name] = val
                        break
    return val


class OpenAIBatchManager:
    def __init__(self, api_key: str | None = None) -> None:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError("Install openai to use OpenAIBatchManager") from exc
        key = api_key or _load_env_key("OPENAI_API_KEY")
        self._client = OpenAI(api_key=key)

    @staticmethod
    def build_item(
        custom_id: str,
        prompt: str,
        model: str,
        max_output_tokens: int = 256,
        reasoning_effort: str | None = None,
        temperature: float | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {
            "model": model,
            "input": prompt,
            "max_output_tokens": max(int(max_output_tokens or 256), 16),
        }
        if reasoning_effort is not None and str(reasoning_effort).lower() != "none_budget":
            body["reasoning"] = {"effort": str(reasoning_effort).lower()}

        is_sol = "sol" in model.lower()
        has_reasoning = "reasoning" in body and body["reasoning"].get("effort") not in (None, "none")
        if temperature is not None and not is_sol and not has_reasoning:
            body["temperature"] = float(temperature)

        return {
            "custom_id": custom_id,
            "method": "POST",
            "url": "/v1/responses",
            "body": body,
        }

    def submit_batch(
        self,
        items: list[dict[str, Any]],
        batch_record_path: Path | str | None = None,
        metadata: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False, encoding="utf-8") as tmp:
            tmp_path = Path(tmp.name)
            for item in items:
                tmp.write(json.dumps(item, ensure_ascii=False) + "\n")

        try:
            with open(tmp_path, "rb") as handle:
                file_obj = self._client.files.create(file=handle, purpose="batch")

            batch_kwargs: dict[str, Any] = {
                "input_file_id": file_obj.id,
                "endpoint": "/v1/responses",
                "completion_window": "24h",
            }
            if metadata:
                batch_kwargs["metadata"] = metadata

            batch = self._client.batches.create(**batch_kwargs)
            record = {
                "provider": "openai",
                "batch_id": batch.id,
                "input_file_id": file_obj.id,
                "status": batch.status,
                "request_count": len(items),
                "created_at": batch.created_at,
                "metadata": metadata or {},
            }
            if batch_record_path:
                Path(batch_record_path).parent.mkdir(parents=True, exist_ok=True)
                Path(batch_record_path).write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
            return record
        finally:
            if tmp_path.exists():
                tmp_path.unlink()

    def check_status(self, batch_id: str) -> dict[str, Any]:
        batch = self._client.batches.retrieve(batch_id)
        counts = getattr(batch, "request_counts", None)
        return {
            "provider": "openai",
            "batch_id": batch.id,
            "status": batch.status,
            "output_file_id": getattr(batch, "output_file_id", None),
            "error_file_id": getattr(batch, "error_file_id", None),
            "total_requests": getattr(counts, "total", 0) if counts else 0,
            "completed_requests": getattr(counts, "completed", 0) if counts else 0,
            "failed_requests": getattr(counts, "failed", 0) if counts else 0,
        }

    def retrieve_results(self, batch_id: str) -> dict[str, dict[str, Any]]:
        status = self.check_status(batch_id)
        if status["status"] != "completed":
            raise RuntimeError(f"Batch {batch_id} not completed (current status: {status['status']})")
        out_id = status["output_file_id"]
        if not out_id:
            raise RuntimeError(f"Batch {batch_id} completed but output_file_id is missing")

        raw_content = self._client.files.content(out_id).text
        results: dict[str, dict[str, Any]] = {}
        for line in raw_content.splitlines():
            line = line.strip()
            if not line:
                continue
            entry = json.loads(line)
            cid = entry["custom_id"]
            resp = entry.get("response", {})
            status_code = resp.get("status_code", 0)
            body = resp.get("body", {})

            text = body.get("output_text") or ""
            if not text:
                output = body.get("output", [])
                if isinstance(output, list):
                    texts = []
                    for item in output:
                        if isinstance(item, dict) and item.get("type") == "message":
                            for c in item.get("content", []):
                                if isinstance(c, dict) and c.get("type") == "output_text" and "text" in c:
                                    texts.append(c["text"])
                    if texts:
                        text = "\n".join(texts)
                elif isinstance(output, str):
                    text = output
            if not text:
                choices = body.get("choices", [])
                if isinstance(choices, list) and choices:
                    text = choices[0].get("message", {}).get("content", "") or ""
            usage = body.get("usage", {})
            in_tokens = usage.get("input_tokens", 0)
            out_tokens = usage.get("output_tokens", 0)
            in_details = usage.get("input_tokens_details", {}) or {}
            out_details = usage.get("output_tokens_details", {}) or {}
            cached_tokens = in_details.get("cached_tokens", 0)
            reasoning_tokens = out_details.get("reasoning_tokens", 0)
            model = body.get("model", "")

            cost = calculate_cost(
                model=model,
                input_tokens=in_tokens,
                output_tokens=out_tokens,
                mode="batch",
                cached_tokens=cached_tokens,
            )

            results[cid] = {
                "custom_id": cid,
                "status_code": status_code,
                "text": text,
                "model": model,
                "request_id": body.get("id"),
                "stop_reason": body.get("status", "completed"),
                "input_tokens": in_tokens,
                "output_tokens": out_tokens,
                "cached_tokens": cached_tokens,
                "reasoning_tokens": reasoning_tokens,
                "calculated_cost": cost,
                "raw_response": body,
                "error": entry.get("error"),
            }
        return results


class AnthropicBatchManager:
    def __init__(self, api_key: str | None = None) -> None:
        try:
            from anthropic import Anthropic
        except ImportError as exc:
            raise RuntimeError("Install anthropic to use AnthropicBatchManager") from exc
        key = api_key or _load_env_key("ANTHROPIC_API_KEY")
        self._client = Anthropic(api_key=key)

    @staticmethod
    def build_item(
        custom_id: str,
        prompt: str,
        model: str,
        max_tokens: int = 256,
        thinking_type: str = "disabled",
        effort: str | None = "low",
    ) -> dict[str, Any]:
        params: dict[str, Any] = {
            "model": model,
            "max_tokens": max(int(max_tokens or 256), 16),
            "messages": [{"role": "user", "content": prompt}],
        }
        if thinking_type in ("disabled", "none"):
            params["thinking"] = {"type": "disabled"}
        elif thinking_type == "between_tools":
            params["thinking"] = {"type": "between_tools"}
        elif thinking_type == "adaptive":
            params["thinking"] = {"type": "adaptive"}
        elif thinking_type == "enabled":
            params["thinking"] = {"type": "enabled", "budget_tokens": 1024}

        if effort:
            params["output_config"] = {"effort": effort}

        return {
            "custom_id": custom_id,
            "params": params,
        }

    def submit_batch(
        self,
        items: list[dict[str, Any]],
        batch_record_path: Path | str | None = None,
    ) -> dict[str, Any]:
        batch = self._client.messages.batches.create(requests=items)
        record = {
            "provider": "anthropic",
            "batch_id": batch.id,
            "status": batch.processing_status,
            "request_count": len(items),
            "created_at": getattr(batch, "created_at", None),
        }
        if batch_record_path:
            Path(batch_record_path).parent.mkdir(parents=True, exist_ok=True)
            Path(batch_record_path).write_text(json.dumps(record, indent=2, default=str) + "\n", encoding="utf-8")
        return record

    def check_status(self, batch_id: str) -> dict[str, Any]:
        batch = self._client.messages.batches.retrieve(batch_id)
        counts = getattr(batch, "request_counts", None)
        return {
            "provider": "anthropic",
            "batch_id": batch.id,
            "status": batch.processing_status,
            "total_requests": getattr(counts, "processing", 0) + getattr(counts, "succeeded", 0) + getattr(counts, "errored", 0) if counts else 0,
            "completed_requests": getattr(counts, "succeeded", 0) if counts else 0,
            "failed_requests": (getattr(counts, "errored", 0) + getattr(counts, "canceled", 0) + getattr(counts, "expired", 0)) if counts else 0,
            "ended_at": getattr(batch, "ended_at", None),
        }

    def retrieve_results(self, batch_id: str) -> dict[str, dict[str, Any]]:
        status = self.check_status(batch_id)
        if status["status"] != "ended":
            raise RuntimeError(f"Anthropic batch {batch_id} not ended (status: {status['status']})")

        results: dict[str, dict[str, Any]] = {}
        for item in self._client.messages.batches.results(batch_id):
            cid = item.custom_id
            res_type = item.result.type
            if res_type == "succeeded":
                msg = item.result.message
                text = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text" or hasattr(b, "text"))
                usage = msg.usage
                in_tokens = getattr(usage, "input_tokens", 0)
                out_tokens = getattr(usage, "output_tokens", 0)
                cached_tokens = getattr(usage, "cache_read_input_tokens", 0)
                out_details = getattr(usage, "output_tokens_details", None)
                reasoning_tokens = getattr(out_details, "thinking_tokens", 0) if out_details else 0
                model = msg.model

                cost = calculate_cost(
                    model=model,
                    input_tokens=in_tokens,
                    output_tokens=out_tokens,
                    mode="batch",
                    cached_tokens=cached_tokens,
                )
                results[cid] = {
                    "custom_id": cid,
                    "status_code": 200,
                    "text": text,
                    "model": model,
                    "request_id": msg.id,
                    "stop_reason": msg.stop_reason,
                    "input_tokens": in_tokens,
                    "output_tokens": out_tokens,
                    "cached_tokens": cached_tokens,
                    "reasoning_tokens": reasoning_tokens,
                    "calculated_cost": cost,
                    "raw_response": msg.model_dump(mode="json"),
                    "error": None,
                }
            else:
                err = getattr(item.result, "error", None)
                results[cid] = {
                    "custom_id": cid,
                    "status_code": getattr(err, "type", 500),
                    "text": "",
                    "model": "",
                    "request_id": None,
                    "stop_reason": res_type,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "cached_tokens": 0,
                    "reasoning_tokens": 0,
                    "calculated_cost": 0.0,
                    "raw_response": {},
                    "error": str(err),
                }
        return results
