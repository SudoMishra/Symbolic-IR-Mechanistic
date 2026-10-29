#!/usr/bin/env python3
"""Generate model-specific YAML configurations for N=500 benchmark expansions."""

from pathlib import Path
import copy
import yaml

ROOT = Path(__file__).resolve().parents[1]

MODELS = {
    "qwen15b": {
        "model_path": "models/qwen2.5-1.5b-instruct-q4_k_m.gguf",
        "model": "Qwen/Qwen2.5-1.5B-Instruct-GGUF:q4_k_m",
        "revision": "d538981f62157dd8d02e8648325a722db3ff9ae8",
        "n_ctx": 8192,
        "n_threads": 12,
        "n_gpu_layers": -1,
        "main_gpu": 0,
        "offload_kqv": True,
        "quantization": "Q4_K_M",
    },
    "qwen35_2b": {
        "model_path": "models/Qwen3.5-2B-Q4_K_M.gguf",
        "model": "unsloth/Qwen3.5-2B-GGUF:q4_k_m",
        "revision": "f6d5376be1edb4d416d56da11e5397a961aca8ae",
        "n_ctx": 8192,
        "n_threads": 12,
        "n_gpu_layers": -1,
        "main_gpu": 0,
        "offload_kqv": True,
        "quantization": "Q4_K_M",
    },
    "qwen35_4b": {
        "model_path": "models/Qwen3.5-4B-Q4_K_M.gguf",
        "model": "unsloth/Qwen3.5-4B-GGUF:q4_k_m",
        "revision": "e87f1764eb865ad3d9be58bc3571d445a6b014ba",
        "n_ctx": 8192,
        "n_threads": 12,
        "n_gpu_layers": -1,
        "main_gpu": 0,
        "offload_kqv": True,
        "quantization": "Q4_K_M",
    },
    "lfm25_12b": {
        "model_path": "models/lfm2.5-1.2b-instruct-q4_k_m.gguf",
        "model": "LiquidAI/LFM2.5-1.2B-Instruct-GGUF:q4_k_m",
        "revision": "b02009280d04ca03d324d084eeeb965a71141315",
        "n_ctx": 8192,
        "n_threads": 12,
        "n_gpu_layers": -1,
        "main_gpu": 0,
        "offload_kqv": True,
        "quantization": "Q4_K_M",
    },
    "lfm25_26b": {
        "model_path": "models/LFM2.5-2.6B-Q4_K_M.gguf",
        "model": "LiquidAI/LFM2.5-2.6B-GGUF:q4_k_m",
        "revision": "e7caca5d835a3901a8e0d63e94009429bafafdfc",
        "n_ctx": 8192,
        "n_threads": 12,
        "n_gpu_layers": -1,
        "main_gpu": 0,
        "offload_kqv": True,
        "assistant_prefill": "<think>\n</think>\n",
        "quantization": "Q4_K_M",
    },
    "gemma4_e2b": {
        "model_path": "models/gemma-4-e2b-it-q4_0.gguf",
        "model": "google/gemma-4-E2B-it-qat-q4_0-gguf",
        "revision": "e67406c117b34f68ebfe9403d527fa28c5bb74ea",
        "n_ctx": 8192,
        "n_threads": 12,
        "n_gpu_layers": -1,
        "main_gpu": 0,
        "offload_kqv": True,
        "quantization": "Q4_0",
    },
    "gemma4_e4b": {
        "model_path": "models/gemma-4-e4b-it-q4_0.gguf",
        "model": "google/gemma-4-E4B-it-qat-q4_0-gguf",
        "revision": "c074be2035ce675c963fb1f71df05a0d31ff6be4",
        "n_ctx": 8192,
        "n_threads": 12,
        "n_gpu_layers": -1,
        "main_gpu": 0,
        "offload_kqv": True,
        "quantization": "Q4_0",
    },
    "tiny_aya": {
        "model_path": "models/tiny-aya-global-q4_k_m.gguf",
        "model": "CohereLabs/tiny-aya-global-GGUF:q4_k_m",
        "revision": "a602ea7eeec3a4ad6f77a1b8cf6a53512824922b",
        "n_ctx": 8192,
        "n_threads": 12,
        "n_gpu_layers": -1,
        "main_gpu": 0,
        "offload_kqv": True,
        "quantization": "Q4_K_M",
    },
}

def generate_stage1_500():
    for tag, m in MODELS.items():
        backend = {
            "type": "llama_cpp",
            "model_path": m["model_path"],
            "model": m["model"],
            "revision": m["revision"],
            "n_ctx": 4096,
            "n_threads": 12,
            "n_gpu_layers": -1,
            "main_gpu": 0,
            "offload_kqv": True,
            "seed": 202610,
        }
        if "assistant_prefill" in m:
            backend["assistant_prefill"] = m["assistant_prefill"]

        cfg = {
            "name": f"01_citation_mve_500_{tag}",
            "seed": 202610,
            "dataset": {
                "family": "citation",
                "count": 500,
                "task_type": "single_hop",
                "grid": {"num_sources": [5, 20]},
            },
            "identifiers": ["structured", "uuid"],
            "backend": backend,
            "generation": {
                "temperature": 0,
                "max_output_tokens": 80,
                "tokenizer": {"type": "llama_cpp", "model_path": m["model_path"]},
            },
            "output_dir": "results/raw",
            "metadata": {
                "stage": 1,
                "scaled_evaluation": True,
                "sample_size": 500,
                "quantization": m["quantization"],
                "execution": "CUDA",
            },
        }
        out_file = ROOT / f"configs/experiments/citation_mve_500_{tag}.yaml"
        out_file.write_text(yaml.dump(cfg, sort_keys=False), encoding="utf-8")
        print(f"Generated {out_file.name}")

def generate_stage8_500():
    for tag, m in MODELS.items():
        backend = {
            "type": "llama_cpp",
            "model_path": m["model_path"],
            "model": m["model"],
            "revision": m["revision"],
            "n_ctx": 8192,
            "n_threads": 12,
            "n_gpu_layers": -1,
            "main_gpu": 0,
            "offload_kqv": True,
            "seed": 202618,
        }
        if "assistant_prefill" in m:
            backend["assistant_prefill"] = m["assistant_prefill"]

        cfg = {
            "name": f"stage8_pii_500_{tag}",
            "seed": 202618,
            "dataset": {
                "family": "pii",
                "count": 250,
                "task_type": "account_resolution",
                "long_context": True,
                "filler_words": 100,
                "prompt_tokens": {"min": 2000, "max": 4200},
                "grid": {"num_sources": [15, 20]},
            },
            "identifiers": ["raw", "random_masked", "untyped", "typed"],
            "backend": backend,
            "generation": {
                "temperature": 0,
                "max_output_tokens": 64,
                "require_citations": False,
                "fixed_source_identifiers": "structured",
                "progress_every": 25,
                "tokenizer": {"type": "llama_cpp", "model_path": m["model_path"]},
            },
            "output_dir": "results/raw",
            "metadata": {
                "stage": 8,
                "scaled_evaluation": True,
                "sample_size": 500,
                "quantization": m["quantization"],
                "execution": "CUDA",
            },
        }
        out_file = ROOT / f"configs/experiments/stage8_pii_500_{tag}.yaml"
        out_file.write_text(yaml.dump(cfg, sort_keys=False), encoding="utf-8")
        print(f"Generated {out_file.name}")

def generate_musique_500():
    for tag, m in MODELS.items():
        backend = {
            "type": "llama_cpp",
            "model_path": m["model_path"],
            "model": m["model"],
            "revision": m["revision"],
            "n_ctx": 8192,
            "n_threads": 12,
            "n_gpu_layers": -1,
            "main_gpu": 0,
            "offload_kqv": True,
            "seed": 202620,
        }
        if "assistant_prefill" in m:
            backend["assistant_prefill"] = m["assistant_prefill"]

        cfg = {
            "name": f"musique_500_{tag}",
            "seed": 202620,
            "dataset": {
                "family": "musique",
                "data_path": "data/musique/musique_ans_v1.0_dev.jsonl",
                "selection_path": "configs/musique/musique_balanced_500.json",
                "count": 500,
                "prompt_tokens": {"min": 1500, "max": 4000},
                "scenarios": [
                    {"name": "scaled_15_sources", "stage": 2, "num_sources": 15, "identifiers": ["numeric", "uuid"]},
                    {"name": "scaled_20_sources", "stage": 2, "num_sources": 20, "identifiers": ["numeric", "uuid"]},
                ],
            },
            "identifiers": ["numeric", "uuid"],
            "backend": backend,
            "generation": {
                "temperature": 0,
                "max_output_tokens": 256,
                "tokenizer": {"type": "llama_cpp", "model_path": m["model_path"]},
            },
            "output_dir": "results/raw",
            "metadata": {
                "stage": "scaled_musique",
                "sample_size": 500,
                "dataset_license": "CC-BY-4.0",
                "execution": "CUDA",
                "quantization": m["quantization"],
            },
        }
        out_file = ROOT / f"configs/musique/musique_500_{tag}.yaml"
        out_file.write_text(yaml.dump(cfg, sort_keys=False), encoding="utf-8")
        print(f"Generated {out_file.name}")

def main():
    generate_stage1_500()
    generate_stage8_500()
    generate_musique_500()

if __name__ == "__main__":
    main()
