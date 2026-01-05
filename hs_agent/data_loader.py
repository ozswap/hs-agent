"""Simple HS codes data loader."""

import pandas as pd

from hs_agent.config.settings import settings
from hs_agent.models import HSCode
from hs_agent.utils.logger import get_logger

logger = get_logger(__name__)


class HSDataLoader:
    """Load and store HS codes data."""

    def __init__(self):
        self.data_dir = settings.data_directory
        self.codes_2digit: dict[str, HSCode] = {}
        self.codes_4digit: dict[str, HSCode] = {}
        self.codes_6digit: dict[str, HSCode] = {}

    def load_all_data(self) -> None:
        """Load HS codes from CSV file."""
        hs_codes_path = self.data_dir / settings.hs_codes_file

        if not hs_codes_path.exists():
            raise FileNotFoundError(f"HS codes file not found: {hs_codes_path}")

        df = pd.read_csv(hs_codes_path)
        failed_count = 0

        for _, row in df.iterrows():
            try:
                code = str(row["hscode"]).strip()
                description = str(row["description"])
                level = int(row["level"])

                hs_code = HSCode(code=code, description=description)

                if level == 2:
                    self.codes_2digit[code] = hs_code
                elif level == 4:
                    self.codes_4digit[code] = hs_code
                elif level == 6:
                    self.codes_6digit[code] = hs_code

            except Exception as e:
                logger.warning(f"Failed to load HS code row: {e}")
                failed_count += 1
                continue

        if failed_count > 0:
            logger.warning(f"Skipped {failed_count} invalid rows during HS code loading")

        logger.info(
            f"Loaded {len(self.codes_2digit)} chapters, "
            f"{len(self.codes_4digit)} headings, "
            f"{len(self.codes_6digit)} subheadings"
        )
