from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from symbolic_ir.analysis import load_jsonl, paired_bootstrap, summarize_file
from symbolic_ir.config import load_config
from symbolic_ir.identifiers import available_conditions
from symbolic_ir.runner import iter_requests, run_experiment


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="symbolic-ir", description="Symbolic identifier research harness")
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("run", help="Run or resume an experiment")
    run.add_argument("--config", required=True)
    run.add_argument("--limit", type=int)
    validate = commands.add_parser("validate", help="Validate and count an experiment")
    validate.add_argument("--config", required=True)
    validate.add_argument("--preview", action="store_true")
    summary = commands.add_parser("summarize", help="Aggregate a raw JSONL result")
    summary.add_argument("path")
    bootstrap = commands.add_parser("bootstrap", help="Paired bootstrap between two conditions")
    bootstrap.add_argument("path")
    bootstrap.add_argument("condition_a")
    bootstrap.add_argument("condition_b")
    bootstrap.add_argument("--metric", default="citation_exact_match")
    bootstrap.add_argument("--samples", type=int, default=10_000)
    commands.add_parser("identifiers", help="List identifier conditions")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "identifiers":
        print("\n".join(available_conditions()))
        return 0
    if args.command == "validate":
        config = load_config(args.config)
        requests = list(iter_requests(config))
        result = {"name": config.name, "digest": config.digest, "requests": len(requests)}
        if args.preview and requests:
            result["preview"] = requests[0][1].prompt
        print(json.dumps(result, indent=2))
        return 0
    if args.command == "run":
        path, counts = run_experiment(load_config(args.config), limit=args.limit)
        print(json.dumps({"output": str(path), **counts}, indent=2))
        return 0
    if args.command == "summarize":
        print(json.dumps(summarize_file(args.path), indent=2, sort_keys=True))
        return 0
    if args.command == "bootstrap":
        effect = paired_bootstrap(load_jsonl(args.path), args.condition_a, args.condition_b, args.metric, samples=args.samples)
        print(json.dumps(asdict(effect), indent=2, sort_keys=True))
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

