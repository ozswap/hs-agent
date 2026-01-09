"""Benchmark runner for HS Agent classification.

Runs benchmark evaluations against a running FastAPI server and outputs
results to the terminal in a clean, copy-paste friendly format.

Usage:
    # Run benchmark (server must be running at localhost:8000)
    uv run python scripts/run_benchmark.py data/benchmarks/benchmark_v1.csv

    # Custom concurrency and API URL
    uv run python scripts/run_benchmark.py data/benchmarks/benchmark_v1.csv --concurrency 5 --api-url http://localhost:8000

    # Output results as JSON
    uv run python scripts/run_benchmark.py data/benchmarks/benchmark_v1.csv --json
"""

import argparse
import asyncio
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

import httpx
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


class BenchmarkRunner:
    """Execute benchmarks against the HS Agent API."""

    def __init__(
        self,
        api_url: str = "http://localhost:8000",
        concurrency: int = 10,
        timeout: float = 600.0,
    ):
        self.api_url = api_url.rstrip("/")
        self.concurrency = concurrency
        self.timeout = timeout

    async def classify_one(self, client: httpx.AsyncClient, product_description: str) -> dict:
        """Classify a single product via the API."""
        try:
            response = await client.post(
                f"{self.api_url}/api/classify",
                json={
                    "product_description": product_description,
                    "high_performance": True,
                    "max_selections": 3,
                },
                timeout=self.timeout,
            )
            if response.status_code == 200:
                data = response.json()
                # Handle both API response formats
                hs_code = data.get("final_code") or data.get("hs_code") or "ERROR"
                confidence = data.get("overall_confidence") or data.get("confidence") or "unknown"
                reasoning = data.get("comparison_summary") or data.get("reasoning") or ""
                return {
                    "hs_code": hs_code,
                    "confidence": confidence,
                    "reasoning": reasoning,
                    "error": None,
                }
            else:
                return {
                    "hs_code": "ERROR",
                    "confidence": "error",
                    "reasoning": f"HTTP {response.status_code}",
                    "error": f"HTTP {response.status_code}",
                }
        except httpx.TimeoutException:
            return {
                "hs_code": "TIMEOUT",
                "confidence": "error",
                "reasoning": "Request timed out",
                "error": "timeout",
            }
        except Exception as e:
            return {
                "hs_code": "ERROR",
                "confidence": "error",
                "reasoning": str(e),
                "error": str(e),
            }

    async def run(self, benchmark_df: pd.DataFrame) -> list[dict]:
        """Run benchmark on all examples with parallel execution."""
        results = []
        total = len(benchmark_df)
        completed = 0
        start_time = time.time()

        semaphore = asyncio.Semaphore(self.concurrency)

        async def process_row(idx: int, row: pd.Series) -> dict:
            nonlocal completed
            async with semaphore:
                row_start = time.time()
                result = await self.classify_one(client, row["product_description"])
                elapsed = time.time() - row_start

                completed += 1

                # Log progress every 10 examples
                if completed % 10 == 0 or completed == total:
                    total_elapsed = time.time() - start_time
                    rate = completed / total_elapsed if total_elapsed > 0 else 0
                    remaining = (total - completed) / rate if rate > 0 else 0
                    logger.info(
                        f"Progress: {completed}/{total} ({completed/total*100:.0f}%) | "
                        f"Rate: {rate:.1f}/min | ETA: {remaining/60:.1f}min"
                    )

                # Normalize HS codes
                predicted_hs6 = (
                    str(result["hs_code"]).zfill(6)
                    if result["hs_code"] not in ["ERROR", "TIMEOUT"]
                    else result["hs_code"]
                )
                ground_truth_hs6 = str(row["ground_truth_hs6"]).zfill(6)

                return {
                    "idx": idx,
                    "product_description": row["product_description"][:80],
                    "ground_truth_hs6": ground_truth_hs6,
                    "predicted_hs6": predicted_hs6,
                    "correct_hs6": predicted_hs6 == ground_truth_hs6,
                    "correct_hs4": predicted_hs6[:4] == ground_truth_hs6[:4]
                    if predicted_hs6 not in ["ERROR", "TIMEOUT"]
                    else False,
                    "correct_hs2": predicted_hs6[:2] == ground_truth_hs6[:2]
                    if predicted_hs6 not in ["ERROR", "TIMEOUT"]
                    else False,
                    "confidence": result["confidence"],
                    "reasoning": result["reasoning"],
                    "error": result["error"],
                    "time_sec": elapsed,
                    "category": row.get("category", "unknown"),
                }

        logger.info(f"Starting benchmark with {total} examples")
        logger.info(
            f"API: {self.api_url} | Concurrency: {self.concurrency} | Timeout: {self.timeout}s"
        )

        async with httpx.AsyncClient() as client:
            tasks = [process_row(idx, row) for idx, row in benchmark_df.iterrows()]
            results = await asyncio.gather(*tasks)

        # Sort by original index
        results.sort(key=lambda x: x["idx"])
        return results


def compute_metrics(results: list[dict]) -> dict:
    """Compute accuracy metrics from results."""
    valid = [r for r in results if r["error"] is None]
    errors = [r for r in results if r["error"] is not None]

    if not valid:
        return {"error": "No valid predictions"}

    hs6_correct = sum(1 for r in valid if r["correct_hs6"])
    hs4_correct = sum(1 for r in valid if r["correct_hs4"])
    hs2_correct = sum(1 for r in valid if r["correct_hs2"])

    # Per-category breakdown
    categories = {}
    for r in valid:
        cat = r["category"]
        if cat not in categories:
            categories[cat] = {"total": 0, "hs6_correct": 0}
        categories[cat]["total"] += 1
        if r["correct_hs6"]:
            categories[cat]["hs6_correct"] += 1

    return {
        "total": len(results),
        "valid": len(valid),
        "errors": len(errors),
        "hs6_accuracy": hs6_correct / len(valid),
        "hs4_accuracy": hs4_correct / len(valid),
        "hs2_accuracy": hs2_correct / len(valid),
        "hs6_correct": hs6_correct,
        "hs4_correct": hs4_correct,
        "hs2_correct": hs2_correct,
        "avg_time_sec": sum(r["time_sec"] for r in valid) / len(valid),
        "by_category": {
            cat: {
                "total": data["total"],
                "accuracy": data["hs6_correct"] / data["total"] if data["total"] > 0 else 0,
            }
            for cat, data in sorted(categories.items())
        },
    }


def print_results(results: list[dict], metrics: dict, show_errors_only: bool = False):
    """Print results in a clean terminal format."""
    print("\n" + "=" * 80)
    print("HS AGENT BENCHMARK RESULTS")
    print("=" * 80)

    # Summary
    print("\nSUMMARY")
    print("-" * 40)
    print(f"Total Examples:    {metrics['total']}")
    print(f"Successful:        {metrics['valid']}")
    print(f"Errors/Timeouts:   {metrics['errors']}")
    print()
    print(
        f"HS6 Accuracy:      {metrics['hs6_accuracy']:.1%} ({metrics['hs6_correct']}/{metrics['valid']})"
    )
    print(
        f"HS4 Accuracy:      {metrics['hs4_accuracy']:.1%} ({metrics['hs4_correct']}/{metrics['valid']})"
    )
    print(
        f"HS2 Accuracy:      {metrics['hs2_accuracy']:.1%} ({metrics['hs2_correct']}/{metrics['valid']})"
    )
    print(f"Avg Time:          {metrics['avg_time_sec']:.1f}s per example")

    # Category breakdown
    if metrics.get("by_category"):
        print("\nBY CATEGORY")
        print("-" * 40)
        for cat, data in metrics["by_category"].items():
            print(f"  {cat:30s} {data['accuracy']:.0%} ({data['total']} examples)")

    # Errors
    errors = [r for r in results if r["error"]]
    if errors:
        print(f"\nERRORS ({len(errors)})")
        print("-" * 40)
        for r in errors[:10]:  # Show first 10
            print(f"  [{r['idx']}] {r['product_description'][:50]}... -> {r['error']}")
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more")

    # Incorrect predictions
    if not show_errors_only:
        incorrect = [r for r in results if not r["correct_hs6"] and not r["error"]]
        if incorrect:
            print(f"\nINCORRECT PREDICTIONS ({len(incorrect)})")
            print("-" * 80)
            print(f"{'#':>4} {'Product':<40} {'Truth':>8} {'Pred':>8} {'Conf':<10}")
            print("-" * 80)
            for r in incorrect[:20]:  # Show first 20
                desc = (
                    r["product_description"][:38] + ".."
                    if len(r["product_description"]) > 40
                    else r["product_description"]
                )
                print(
                    f"{r['idx']:4d} {desc:<40} {r['ground_truth_hs6']:>8} {r['predicted_hs6']:>8} {r['confidence']:<10}"
                )
            if len(incorrect) > 20:
                print(f"... and {len(incorrect) - 20} more incorrect predictions")

    print("\n" + "=" * 80)


def print_json(results: list[dict], metrics: dict):
    """Print results as JSON for piping/parsing."""
    output = {
        "timestamp": datetime.now().isoformat(),
        "metrics": metrics,
        "results": results,
    }
    print(json.dumps(output, indent=2, default=str))


async def main():
    parser = argparse.ArgumentParser(description="Run HS Agent benchmark evaluation")
    parser.add_argument(
        "benchmark_file",
        type=Path,
        help="Path to benchmark CSV file",
    )
    parser.add_argument(
        "--api-url",
        default="http://localhost:8000",
        help="API server URL (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=10,
        help="Number of concurrent requests (default: 10)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=600.0,
        help="Request timeout in seconds (default: 600)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON",
    )
    parser.add_argument(
        "--errors-only",
        action="store_true",
        help="Only show errors in output",
    )

    args = parser.parse_args()

    # Load benchmark data
    if not args.benchmark_file.exists():
        logger.error(f"Benchmark file not found: {args.benchmark_file}")
        sys.exit(1)

    benchmark_df = pd.read_csv(args.benchmark_file)
    logger.info(f"Loaded {len(benchmark_df)} examples from {args.benchmark_file}")

    # Validate required columns
    required_cols = ["product_description", "ground_truth_hs6"]
    missing = [c for c in required_cols if c not in benchmark_df.columns]
    if missing:
        logger.error(f"Missing required columns: {missing}")
        sys.exit(1)

    # Run benchmark
    runner = BenchmarkRunner(
        api_url=args.api_url,
        concurrency=args.concurrency,
        timeout=args.timeout,
    )

    start = time.time()
    results = await runner.run(benchmark_df)
    elapsed = time.time() - start

    logger.info(f"Benchmark completed in {elapsed/60:.1f} minutes")

    # Compute metrics
    metrics = compute_metrics(results)
    metrics["total_time_sec"] = elapsed

    # Output results
    if args.json:
        print_json(results, metrics)
    else:
        print_results(results, metrics, show_errors_only=args.errors_only)


if __name__ == "__main__":
    asyncio.run(main())
