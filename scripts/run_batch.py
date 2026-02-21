"""Batch API runner for solicitation analysis.

Uses the Anthropic Message Batches API for 50% cost savings on high-volume runs.
Prepares batch requests, submits them, polls for completion, and saves results.

Usage:
    uv run python scripts/run_batch.py --limit 100
    uv run python scripts/run_batch.py --batch-id msgbatch_abc123  # resume polling
"""

import argparse
import json
import logging
import sys
from pathlib import Path

from dotenv import load_dotenv

from spotting_concrete_boats.analyzer import SolicitationAnalyzer
from spotting_concrete_boats.documents import (
    build_document_blocks,
    load_and_prepare_opportunities,
)

logger = logging.getLogger(__name__)

DEFAULT_DATA_DIR = Path("data")
DEFAULT_RESULTS_DIR = DEFAULT_DATA_DIR / "results"


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Run solicitation analysis via Anthropic Batch API."
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Process at most N solicitations.",
    )
    parser.add_argument(
        "--offset",
        type=int,
        default=0,
        help="Skip the first N solicitations before processing.",
    )
    parser.add_argument(
        "--batch-id",
        type=str,
        default=None,
        help="Resume polling an existing batch by ID (skip prepare/submit).",
    )
    parser.add_argument(
        "--poll-interval",
        type=int,
        default=60,
        help="Seconds between batch status checks (default: 60).",
    )
    parser.add_argument(
        "--results-dir",
        type=Path,
        default=DEFAULT_RESULTS_DIR,
        help=f"Directory for per-solicitation result JSON files (default: {DEFAULT_RESULTS_DIR}).",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=DEFAULT_DATA_DIR,
        help=f"Base data directory (default: {DEFAULT_DATA_DIR}).",
    )
    parser.add_argument(
        "--prepare-only",
        action="store_true",
        help="Prepare batch requests and save to disk without submitting.",
    )
    return parser.parse_args()


def save_results(
    batch_results: dict[str, dict[str, dict]],
    results_dir: Path,
    title_map: dict[str, str],
) -> int:
    """Save batch results as per-solicitation JSON files.

    Args:
        batch_results: Dict mapping notice_id → {prompt_name: result_dict}.
        results_dir: Output directory.
        title_map: Dict mapping notice_id → title for metadata.

    Returns:
        Number of files written.
    """
    from spotting_concrete_boats.prompts import SEVERITY_LABELS, STRENGTH_LABELS

    results_dir.mkdir(parents=True, exist_ok=True)
    written = 0

    for notice_id, prompt_results in batch_results.items():
        # Add score labels
        for prompt_data in prompt_results.values():
            if "severity" in prompt_data:
                prompt_data["severity_label"] = SEVERITY_LABELS.get(prompt_data["severity"], "")
            elif "strength" in prompt_data:
                prompt_data["strength_label"] = STRENGTH_LABELS.get(prompt_data["strength"], "")

        result_data = {
            "notice_id": notice_id,
            "title": title_map.get(notice_id, ""),
            "results": prompt_results,
        }
        result_path = results_dir / f"{notice_id}.json"
        with open(result_path, "w") as f:
            json.dump(result_data, f, indent=2)
        written += 1

    return written


def main() -> None:
    """Run the batch analysis pipeline."""
    load_dotenv()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    args = parse_args()
    results_dir: Path = args.results_dir
    data_dir: Path = args.data_dir

    analyzer = SolicitationAnalyzer()

    # If resuming an existing batch, skip straight to polling
    if args.batch_id:
        logger.info("Resuming batch %s — polling for results...", args.batch_id)
        batch_results = analyzer.poll_batch(args.batch_id, poll_interval=args.poll_interval)
        written = save_results(batch_results, results_dir, title_map={})
        logger.info("Saved %d result files to %s", written, results_dir)
        return

    opportunities_path = data_dir / "opportunities.json"
    attachments_dir = data_dir / "attachments"

    if not opportunities_path.exists():
        logger.error("Opportunities file not found: %s", opportunities_path)
        sys.exit(1)

    # Load and prepare
    df = load_and_prepare_opportunities(opportunities_path, attachments_dir)
    df_analyzable = df[df["analyzable"]].copy().reset_index(drop=True)

    if args.offset > 0:
        df_analyzable = df_analyzable.iloc[args.offset :].reset_index(drop=True)
    if args.limit is not None:
        df_analyzable = df_analyzable.iloc[: args.limit].copy()

    # Skip already-analyzed
    results_dir.mkdir(parents=True, exist_ok=True)
    already_done = {p.stem for p in results_dir.glob("*.json")}
    to_analyze = df_analyzable[~df_analyzable["noticeId"].isin(already_done)].copy()

    skipped = len(df_analyzable) - len(to_analyze)
    if skipped > 0:
        logger.info("Skipping %d already-analyzed records", skipped)

    if to_analyze.empty:
        logger.info("Nothing to analyze — all selected solicitations already have results.")
        return

    # Build document blocks for each solicitation
    solicitations = []
    title_map = {}
    for _, row in to_analyze.iterrows():
        notice_id = row["noticeId"]
        file_paths = row["attachment_paths"]
        context = row["context"] if row["context"] else None
        blocks = build_document_blocks(file_paths, description=context)
        if blocks:
            solicitations.append({"notice_id": notice_id, "document_blocks": blocks})
            title_map[notice_id] = row.get("title", "")

    logger.info("Built document blocks for %d solicitations", len(solicitations))

    # Prepare batch requests
    batch_requests = analyzer.prepare_batch_requests(solicitations)

    if args.prepare_only:
        output_path = data_dir / "batch_requests.json"
        with open(output_path, "w") as f:
            json.dump(batch_requests, f, indent=2)
        logger.info("Saved %d batch requests to %s", len(batch_requests), output_path)
        return

    # Submit
    batch_id = analyzer.submit_batch(batch_requests)
    logger.info("Batch submitted: %s", batch_id)

    # Poll and save
    batch_results = analyzer.poll_batch(batch_id, poll_interval=args.poll_interval)
    written = save_results(batch_results, results_dir, title_map)
    logger.info("Done. Saved %d result files to %s", written, results_dir)


if __name__ == "__main__":
    main()
