"""CLI entry point for running evaluations.

Usage:
    python -m eval.run_eval --split conflicting --n-samples 3 --limit 50
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

from rich.console import Console
from rich.table import Table

import config
from eval.evaluator import run_evaluation

console = Console()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run DeepSeek-R1 inference on ImpossibleBench LiveCodeBench"
    )
    parser.add_argument(
        "--split",
        choices=["original", "conflicting", "one_off"],
        default="one_off",
        help="Dataset split to evaluate",
    )
    parser.add_argument(
        "--n-samples",
        type=int,
        default=config.N_SAMPLES,
        help="Number of samples per problem",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Max number of problems to evaluate (None = all)",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=config.TEMPERATURE,
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=config.MAX_TOKENS,
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output JSONL path (default: data/rollouts/<split>_<timestamp>.jsonl)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.output is None:
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        args.output = config.ROLLOUTS_DIR / f"{args.split}_{ts}.jsonl"

    args.output.parent.mkdir(parents=True, exist_ok=True)

    console.print(f"[bold green]Starting eval[/bold green]")
    console.print(f"  Split:       {args.split}")
    console.print(f"  Limit:       {args.limit or 'all'}")
    console.print(f"  N-samples:   {args.n_samples}")
    console.print(f"  Temperature: {args.temperature}")
    console.print(f"  Max tokens:  {args.max_tokens}")
    console.print(f"  Output:      {args.output}")
    console.print()

    summary = run_evaluation(
        args.split,
        n_samples=args.n_samples,
        limit=args.limit,
        output_path=args.output,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
    )

    table = Table(title="Eval Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="magenta")
    table.add_row("Total rollouts", str(summary["total"]))
    table.add_row("Pass original tests", str(summary["pass_original"]))
    table.add_row("Pass impossible tests", str(summary["pass_impossible"]))
    table.add_row(
        "Cheating rate",
        f"{summary['cheating_rate']:.1%}",
    )
    table.add_row("Output file", summary["output_path"])
    console.print(table)


if __name__ == "__main__":
    main()
