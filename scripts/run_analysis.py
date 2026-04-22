"""Batch runner for solicitation analysis.

Replaces the notebook as the execution engine for full-scale runs. Loads
opportunities, runs the analyzer on each, and saves per-solicitation results
to disk with checkpointing (skips already-analyzed records).

Usage:
    uv run python scripts/run_analysis.py --limit 10
    uv run python scripts/run_analysis.py --dry-run
    uv run python scripts/run_analysis.py --results-dir data/results_v2
"""

import argparse
import csv
import json
import logging
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

from spotting_concrete_boats.analyzer import SolicitationAnalyzer
from spotting_concrete_boats.documents import load_and_prepare_opportunities

logger = logging.getLogger(__name__)

DEFAULT_DATA_DIR = Path("data")
DEFAULT_RESULTS_DIR = DEFAULT_DATA_DIR / "results"


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Run solicitation analysis on SAM.gov opportunities."
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
        "--dry-run",
        action="store_true",
        help="Show what would be analyzed without calling the API.",
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
        help=f"Base data directory containing opportunities.json and attachments/ "
        f"(default: {DEFAULT_DATA_DIR}).",
    )
    return parser.parse_args()


def write_summary_csv(results_dir: Path, output_path: Path) -> None:
    """Read all result JSON files and write a one-row-per-solicitation summary CSV."""
    result_files = sorted(results_dir.glob("*.json"))
    if not result_files:
        logger.warning("No result files found in %s — skipping summary CSV.", results_dir)
        return

    rows = []
    for result_file in result_files:
        with open(result_file, encoding="utf-8") as f:
            data = json.load(f)

        notice_id = data.get("notice_id", result_file.stem)
        title = data.get("title", "")
        results = data.get("results", {})

        row = {"notice_id": notice_id, "title": title}

        for prompt_name, prompt_data in results.items():
            if "severity" in prompt_data:
                row[f"{prompt_name}_score"] = prompt_data["severity"]
                row[f"{prompt_name}_label"] = prompt_data.get("severity_label", "")
            elif "strength" in prompt_data:
                row[f"{prompt_name}_score"] = prompt_data["strength"]
                row[f"{prompt_name}_label"] = prompt_data.get("strength_label", "")
            if "sufficient_content" in prompt_data:
                row[f"{prompt_name}_sufficient"] = prompt_data["sufficient_content"]
            if "evidence" in prompt_data:
                row[f"{prompt_name}_evidence_count"] = len(prompt_data["evidence"])

        rows.append(row)

    if not rows:
        return

    # Collect all column names across all rows for a consistent CSV header
    all_columns = list(dict.fromkeys(col for row in rows for col in row.keys()))

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=all_columns)
        writer.writeheader()
        writer.writerows(rows)

    logger.info("Wrote summary CSV with %d rows to %s", len(rows), output_path)


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

    opportunities_path = data_dir / "opportunities.json"
    attachments_dir = data_dir / "attachments"

    if not opportunities_path.exists():
        logger.error("Opportunities file not found: %s", opportunities_path)
        sys.exit(1)

    # Load and prepare opportunities
    df = load_and_prepare_opportunities(opportunities_path, attachments_dir)
    df_analyzable = df[df["analyzable"]].copy().reset_index(drop=True)

    # Apply offset and limit
    if args.offset > 0:
        df_analyzable = df_analyzable.iloc[args.offset :].reset_index(drop=True)
    if args.limit is not None:
        df_analyzable = df_analyzable.iloc[: args.limit].copy()

    logger.info("Selected %d opportunities for analysis", len(df_analyzable))

    # Check which have already been analyzed
    results_dir.mkdir(parents=True, exist_ok=True)
    already_done = {p.stem for p in results_dir.glob("*.json")}
    to_analyze = df_analyzable[~df_analyzable["noticeId"].isin(already_done)].copy()

    skipped = len(df_analyzable) - len(to_analyze)
    if skipped > 0:
        logger.info("Skipping %d already-analyzed records (results on disk)", skipped)

    if args.dry_run:
        print(f"\n{'='*80}")
        print(f"DRY RUN — {len(to_analyze)} solicitations would be analyzed:\n")
        for idx, row in to_analyze.iterrows():
            notice_id = row["noticeId"]
            title = row.get("title", "Untitled")
            n_files = row["attachment_count"]
            pages = row.get("total_pages", 0)
            print(f"  [{idx + 1}] {notice_id[:12]}… — {title}")
            print(f"       {n_files} attachments, {int(pages)} pages")
        print(f"\n{'='*80}")
        print(f"Total: {len(to_analyze)} to analyze, {skipped} already done")
        return

    if to_analyze.empty:
        logger.info("All %d selected solicitations already analyzed. Nothing to do.", skipped)
        write_summary_csv(results_dir, results_dir / "results_summary.csv")
        return

    # Initialize analyzer
    analyzer = SolicitationAnalyzer()
    logger.info("Analyzer ready: %s", analyzer)

    succeeded = 0
    failed = 0
    start_time = time.time()

    for i, (_, row) in enumerate(to_analyze.iterrows()):
        notice_id = row["noticeId"]
        title = row.get("title", "Untitled")
        file_paths = row["attachment_paths"]
        context = row["context"] if row["context"] else None

        logger.info(
            "[%d/%d] Analyzing: %s — %s",
            i + 1,
            len(to_analyze),
            notice_id[:12],
            title,
        )

        try:
            results = analyzer.analyze_from_files(file_paths, description=context)

            # Add score labels for sins/virtues
            for prompt_name, prompt_data in results.items():
                if "severity" in prompt_data:
                    from spotting_concrete_boats.prompts import SEVERITY_LABELS

                    prompt_data["severity_label"] = SEVERITY_LABELS.get(prompt_data["severity"], "")
                elif "strength" in prompt_data:
                    from spotting_concrete_boats.prompts import STRENGTH_LABELS

                    prompt_data["strength_label"] = STRENGTH_LABELS.get(prompt_data["strength"], "")

            # Save result to disk
            result_data = {
                "notice_id": notice_id,
                "title": title,
                "results": results,
            }
            result_path = results_dir / f"{notice_id}.json"
            with open(result_path, "w", encoding="utf-8") as f:
                json.dump(result_data, f, indent=2)

            succeeded += 1
            logger.info("  Saved: %s", result_path)

        except Exception as e:
            failed += 1
            logger.warning("  Error analyzing %s: %s", notice_id, e)

    elapsed = time.time() - start_time
    logger.info(
        "Done. %d succeeded, %d failed (%.1f min elapsed).",
        succeeded,
        failed,
        elapsed / 60,
    )

    # Write summary CSV
    write_summary_csv(results_dir, results_dir / "results_summary.csv")


if __name__ == "__main__":
    main()
