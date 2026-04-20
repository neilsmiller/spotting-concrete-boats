"""Download SBA solicitations from SAM.gov filtered by Product Service Codes."""

import argparse
import logging
import os
from datetime import datetime, timedelta

from dotenv import load_dotenv

from spotting_concrete_boats.sam import SAMClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")

# Product Service Codes covering SBA-relevant categories
CLASSIFICATION_CODES = "D,7A,7B,7C,7D,7E,7F,7G,7H,7J,7K,A,B,G,R,L"


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    today = datetime.now()
    default_from = (today - timedelta(days=30)).strftime("%m/%d/%Y")
    default_to = today.strftime("%m/%d/%Y")

    parser = argparse.ArgumentParser(description="Download SBA solicitations from SAM.gov")
    parser.add_argument(
        "--from-date",
        default=default_from,
        help="Start date in MM/DD/YYYY format (default: 30 days ago)",
    )
    parser.add_argument(
        "--to-date",
        default=default_to,
        help="End date in MM/DD/YYYY format (default: today)",
    )
    parser.add_argument(
        "--output-dir",
        default="data/attachments",
        help="Directory for downloaded attachments (default: data/attachments)",
    )
    parser.add_argument(
        "--output-json",
        default="data/opportunities.json",
        help="Path for output JSON file (default: data/opportunities.json)",
    )
    return parser.parse_args()


def main() -> None:
    """Run the solicitation download pipeline."""
    load_dotenv()

    api_key = os.environ.get("SAM_API_KEY")
    if not api_key:
        raise ValueError("SAM_API_KEY not found in environment. Add it to your .env file.")

    args = parse_args()

    client = SAMClient(api_key)
    client.fetch_and_save(
        posted_from=args.from_date,
        posted_to=args.to_date,
        output_path=args.output_json,
        attachments_dir=args.output_dir,
        csv_cache_path="data/sam_full_export.csv",
        classification_code=CLASSIFICATION_CODES,
    )


if __name__ == "__main__":
    main()
