"""Data access layer for HS Agent.

This module provides data loading and access utilities:
- HSDataLoader: Load HS codes from CSV files
- ChapterNotesService: Load chapter notes from markdown files
"""

from .chapter_notes import ChapterNotesService
from .loader import HSDataLoader

__all__ = [
    "HSDataLoader",
    "ChapterNotesService",
]
