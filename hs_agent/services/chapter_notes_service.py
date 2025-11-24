"""Service for loading HS chapter notes from markdown files.

Chapter notes contain important information about:
- Scope and coverage of each chapter
- Exclusions and exceptions
- Cross-references to other chapters
- Trade classification rules and precedence
"""

from pathlib import Path
from typing import List

from hs_agent.utils.logger import get_logger

logger = get_logger("hs_agent.services.chapter_notes")


class ChapterNotesService:
    """Service for loading and managing HS chapter notes."""

    def __init__(self, notes_directory: str = "data/chapters_markdown"):
        """Initialize the chapter notes service.

        Args:
            notes_directory: Path to directory containing chapter note markdown files
        """
        self.notes_dir = Path(notes_directory)

    def load_chapter_notes(self, chapter_codes: List[str]) -> str:
        """Load chapter notes for given chapter codes.

        Args:
            chapter_codes: List of 2-digit chapter codes (e.g., ['85', '92'])

        Returns:
            Formatted string with chapter notes, or message if unavailable

        Example:
            >>> service = ChapterNotesService()
            >>> notes = service.load_chapter_notes(['85', '92'])
            >>> print(notes)
            ═══ CHAPTER 85 NOTES ═══
            Electrical machinery and equipment...

            ═══ CHAPTER 92 NOTES ═══
            Musical instruments...
        """
        if not self.notes_dir.exists():
            logger.warning(f"⚠️  Chapter notes directory not found: {self.notes_dir}")
            return "Chapter notes not available."

        chapter_notes = []

        # Remove duplicates and sort for consistent output
        for chapter_code in sorted(set(chapter_codes)):
            # Format: chapter_01_notes.md, chapter_85_notes.md, etc.
            notes_file = self.notes_dir / f"chapter_{chapter_code}_notes.md"

            if notes_file.exists():
                try:
                    with open(notes_file, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                        chapter_notes.append(f"═══ CHAPTER {chapter_code} NOTES ═══\n{content}")
                except Exception as e:
                    logger.warning(f"⚠️  Failed to load notes for chapter {chapter_code}: {e}")
            else:
                logger.debug(f"Notes file not found for chapter {chapter_code}: {notes_file}")

        if not chapter_notes:
            return "No chapter notes available for the chapters in these paths."

        return "\n\n".join(chapter_notes)
