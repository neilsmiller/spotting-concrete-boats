"""SAM.gov API client for searching and downloading solicitation data."""

import csv
import json
import logging
import re
from io import StringIO
from pathlib import Path
from typing import Any

import requests

logger = logging.getLogger(__name__)


def sanitize_filename(filename: str) -> str:
    """Remove invalid characters from a filename."""
    return re.sub(r'[<>:"/\\|?*]', "_", filename)


def _parse_content_disposition(header: str) -> str:
    """Extract filename from a Content-Disposition header.

    Handles both standard and non-standard header formats.
    """
    if not header:
        return "unknown_file"

    # Try standard format: filename="..."
    match = re.search(r'filename[*]?=["\']?([^"\';\r\n]+)', header)
    if match:
        return match.group(1).strip()

    # Fallback: take everything after the last '='
    if "=" in header:
        return header.rsplit("=", 1)[-1].strip().strip("\"'")

    return "unknown_file"


class SAMClient:
    """Client for interacting with the SAM.gov Opportunities API."""

    BASE_URL = "https://api.sam.gov/prod/opportunities/v2/search"
    CSV_URL = (
        "https://sam.gov/api/prod/fileextractservices/v1/api/download/"
        "Contract%20Opportunities/datagov/ContractOpportunitiesFullCSV.csv"
        "?privacy=Public"
    )

    # Posting types we care about for solicitation analysis
    # p = Presolicitation, o = Solicitation, k = Combined Synopsis/Solicitation
    # https://open.gsa.gov/api/get-opportunities-public-api/
    ALL_POSTING_TYPES = "p,o,k"

    PAGE_SIZE = 1000  # API maximum per request

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = requests.Session()

    def _build_params(
        self,
        posted_from: str,
        posted_to: str,
        organization_code: str | None = None,
        posting_types: str | None = None,
        naics_code: str | None = None,
        set_aside: str | None = None,
        status: str | None = None,
        keyword: str | None = None,
        classification_code: str | None = None,
        response_deadline_from: str | None = None,
        response_deadline_to: str | None = None,
    ) -> dict[str, Any]:
        """Build query parameters for the SAM.gov API.

        Args:
            posted_from: Start date in MM/DD/YYYY format.
            posted_to: End date in MM/DD/YYYY format.
            organization_code: Agency/org code to filter by (e.g., "070" for SBA).
            posting_types: Comma-separated posting type codes. Defaults to all types.
            naics_code: NAICS industry code filter (e.g., "541512").
            set_aside: Set-aside type code (e.g., "SBA" for small business).
            status: Opportunity status filter (e.g., "active", "archived").
            keyword: Full-text keyword search.
            classification_code: Product/service classification code (e.g., "70" for IT).
            response_deadline_from: Response deadline start in MM/DD/YYYY format.
            response_deadline_to: Response deadline end in MM/DD/YYYY format.

        Returns:
            Dictionary of API query parameters.
        """
        params: dict[str, Any] = {
            "api_key": self.api_key,
            "limit": self.PAGE_SIZE,
            "postedFrom": posted_from,
            "postedTo": posted_to,
            "ptype": posting_types or self.ALL_POSTING_TYPES,
        }

        # Map keyword args to SAM.gov API parameter names
        optional_mappings = {
            "organizationCode": organization_code,
            "ncode": naics_code,
            "typeOfSetAside": set_aside,
            "status": status,
            "q": keyword,
            "classificationCode": classification_code,
            "rdlfrom": response_deadline_from,
            "rdlto": response_deadline_to,
        }
        for api_name, value in optional_mappings.items():
            if value is not None:
                params[api_name] = value

        return params

    def search(
        self,
        posted_from: str,
        posted_to: str,
        organization_code: str | None = None,
        posting_types: str | None = None,
        naics_code: str | None = None,
        set_aside: str | None = None,
        status: str | None = None,
        keyword: str | None = None,
        classification_code: str | None = None,
        response_deadline_from: str | None = None,
        response_deadline_to: str | None = None,
    ) -> list[dict[str, Any]]:
        """Search SAM.gov for contract opportunities with auto-pagination.

        Fetches all matching results by paginating through the API automatically.
        The API returns a maximum of 1000 results per request.

        Args:
            posted_from: Start date in MM/DD/YYYY format.
            posted_to: End date in MM/DD/YYYY format.
            organization_code: Agency/org code to filter by (e.g., "070" for SBA).
            posting_types: Comma-separated posting type codes. Defaults to all types.
            naics_code: NAICS industry code filter (e.g., "541512").
            set_aside: Set-aside type code (e.g., "SBA" for small business).
            status: Opportunity status filter (e.g., "active", "archived").
            keyword: Full-text keyword search.
            classification_code: Product/service classification code (e.g., "70" for IT).
            response_deadline_from: Response deadline start in MM/DD/YYYY format.
            response_deadline_to: Response deadline end in MM/DD/YYYY format.

        Returns:
            List of raw opportunity records from the API.
        """
        params = self._build_params(
            posted_from=posted_from,
            posted_to=posted_to,
            organization_code=organization_code,
            posting_types=posting_types,
            naics_code=naics_code,
            set_aside=set_aside,
            status=status,
            keyword=keyword,
            classification_code=classification_code,
            response_deadline_from=response_deadline_from,
            response_deadline_to=response_deadline_to,
        )

        all_opportunities: list[dict[str, Any]] = []
        offset = 0

        while True:
            params["offset"] = offset
            response = self.session.get(self.BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()

            if "opportunitiesData" not in data:
                raise ValueError(
                    f"SAM.gov API response missing 'opportunitiesData'. Response: {data}"
                )

            page = data["opportunitiesData"]
            total = data.get("totalRecords", len(page))
            all_opportunities.extend(page)
            logger.info("Fetched %d/%d opportunities...", len(all_opportunities), total)

            if len(all_opportunities) >= total or len(page) < self.PAGE_SIZE:
                break

            offset += self.PAGE_SIZE

        return all_opportunities

    def download_attachments(
        self,
        opportunities: list[dict[str, Any]],
        output_dir: str = "attachments",
        max_per_opportunity: int = 5,
    ) -> list[dict[str, Any]]:
        """Download attachments for a list of opportunities.

        Mutates each opportunity record in-place by adding a 'downloadedFiles' list
        and an 'office' alias. Skips files that already exist on disk.

        Args:
            opportunities: List of raw opportunity records from search().
            output_dir: Directory to save downloaded files.
            max_per_opportunity: Max attachments to download per opportunity.

        Returns:
            The same list of opportunity records, with download info added.
        """
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        for opp in opportunities:
            # Add office alias for backward compat with analysis.py
            opp["office"] = opp.get("fullParentPathName", "Not specified")

            resource_links = opp.get("resourceLinks", [])
            downloaded_files: list[str] = []

            if resource_links:
                for url in resource_links[:max_per_opportunity]:
                    try:
                        # Peek at filename via HEAD to check if already downloaded
                        notice_id = opp.get("noticeId", "unknown")

                        resp = self.session.get(url, stream=True)
                        resp.raise_for_status()

                        original_filename = _parse_content_disposition(
                            resp.headers.get("Content-Disposition", "")
                        )
                        filename = f"{notice_id}_{sanitize_filename(original_filename)}"
                        filepath = Path(output_dir) / filename

                        if filepath.exists():
                            downloaded_files.append(filename)
                            continue

                        with open(filepath, "wb") as f:
                            for chunk in resp.iter_content(chunk_size=8192):
                                if chunk:
                                    f.write(chunk)

                        downloaded_files.append(filename)
                    except Exception as e:
                        logger.warning(
                            "Failed to download attachment for %s: %s",
                            opp.get("noticeId"),
                            e,
                        )

            opp["downloadedFiles"] = downloaded_files

        return opportunities

    def enrich_with_descriptions(
        self,
        opportunities: list[dict[str, Any]],
        csv_path: str | None = None,
    ) -> list[dict[str, Any]]:
        """Enrich opportunity records with description text from SAM.gov's full CSV export.

        If csv_path is provided and the file exists, reads from disk instead of
        re-downloading. If downloading, saves to csv_path for next time.

        Args:
            opportunities: List of opportunity records (must have 'noticeId' field).
            csv_path: Optional path to cache the CSV file on disk.

        Returns:
            The same list with 'description' field added to each record.
        """
        notice_ids = {opp["noticeId"] for opp in opportunities}
        descriptions: dict[str, str] = {}

        if csv_path and Path(csv_path).exists():
            logger.info("Reading cached CSV from %s", csv_path)
            csv_text = Path(csv_path).read_text()
        else:
            logger.info("Downloading SAM.gov full CSV export...")
            response = self.session.get(self.CSV_URL)
            response.raise_for_status()
            csv_text = response.text

            if csv_path:
                Path(csv_path).parent.mkdir(parents=True, exist_ok=True)
                Path(csv_path).write_text(csv_text)
                logger.info("Cached CSV to %s", csv_path)

        reader = csv.DictReader(StringIO(csv_text))
        for row in reader:
            if row["NoticeId"] in notice_ids:
                descriptions[row["NoticeId"]] = row["Description"]
                if len(descriptions) == len(notice_ids):
                    break

        for opp in opportunities:
            opp["description"] = descriptions.get(opp["noticeId"], "")

        return opportunities

    def fetch_and_save(
        self,
        posted_from: str,
        posted_to: str,
        output_path: str = "opportunities.json",
        attachments_dir: str = "attachments",
        enrich: bool = True,
        csv_cache_path: str | None = None,
        **search_kwargs: Any,
    ) -> list[dict[str, Any]]:
        """End-to-end: search, download attachments, enrich, and save to JSON.

        Convenience method that chains search -> download -> enrich -> save.

        Args:
            posted_from: Start date in MM/DD/YYYY format.
            posted_to: End date in MM/DD/YYYY format.
            output_path: Path to save the output JSON.
            attachments_dir: Directory to save downloaded attachments.
            enrich: Whether to fetch descriptions from the full CSV.
            csv_cache_path: Optional path to cache the enrichment CSV on disk.
            **search_kwargs: Additional filters passed to search()
                (e.g., organization_code, naics_code, keyword, etc.).

        Returns:
            List of enriched opportunity records.
        """
        logger.info("Searching SAM.gov for opportunities %s - %s...", posted_from, posted_to)
        opportunities = self.search(posted_from, posted_to, **search_kwargs)
        logger.info("Found %d opportunities", len(opportunities))

        logger.info("Downloading attachments to %s/...", attachments_dir)
        self.download_attachments(opportunities, attachments_dir)

        if enrich and opportunities:
            logger.info("Enriching with descriptions from SAM.gov CSV...")
            self.enrich_with_descriptions(opportunities, csv_path=csv_cache_path)

        with open(output_path, "w") as f:
            json.dump(opportunities, f, indent=2)
        logger.info("Saved %d opportunities to %s", len(opportunities), output_path)

        return opportunities
