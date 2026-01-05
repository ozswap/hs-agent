"""Tests for ChapterNotesService.

Tests cover:
- Service initialization
- Loading chapter notes from files
- Deduplication and sorting of chapter codes
- Graceful handling of missing files/directories
"""

from pathlib import Path


from hs_agent.services.chapter_notes_service import ChapterNotesService


class TestChapterNotesServiceInit:
    """Tests for ChapterNotesService initialization."""

    def test_default_directory(self):
        """Test default notes directory."""
        service = ChapterNotesService()

        assert service.notes_dir == Path("data/chapters_markdown")

    def test_custom_directory(self):
        """Test custom notes directory."""
        service = ChapterNotesService(notes_directory="/custom/path")

        assert service.notes_dir == Path("/custom/path")


class TestLoadChapterNotes:
    """Tests for load_chapter_notes method."""

    def test_loads_single_chapter(self, tmp_path):
        """Test loading a single chapter's notes."""
        # Create chapter notes file
        notes_file = tmp_path / "chapter_84_notes.md"
        notes_file.write_text("This chapter covers machinery.")

        service = ChapterNotesService(notes_directory=str(tmp_path))

        result = service.load_chapter_notes(["84"])

        assert "═══ CHAPTER 84 NOTES ═══" in result
        assert "This chapter covers machinery." in result

    def test_loads_multiple_chapters(self, tmp_path):
        """Test loading multiple chapters' notes."""
        # Create chapter notes files
        (tmp_path / "chapter_84_notes.md").write_text("Machinery chapter.")
        (tmp_path / "chapter_85_notes.md").write_text("Electrical chapter.")

        service = ChapterNotesService(notes_directory=str(tmp_path))

        result = service.load_chapter_notes(["84", "85"])

        assert "═══ CHAPTER 84 NOTES ═══" in result
        assert "Machinery chapter." in result
        assert "═══ CHAPTER 85 NOTES ═══" in result
        assert "Electrical chapter." in result

    def test_deduplicates_chapter_codes(self, tmp_path):
        """Test that duplicate chapter codes are removed."""
        (tmp_path / "chapter_84_notes.md").write_text("Machinery content.")

        service = ChapterNotesService(notes_directory=str(tmp_path))

        # Pass duplicates
        result = service.load_chapter_notes(["84", "84", "84"])

        # Should only appear once
        assert result.count("═══ CHAPTER 84 NOTES ═══") == 1

    def test_sorts_chapter_codes(self, tmp_path):
        """Test that chapter codes are sorted in output."""
        (tmp_path / "chapter_01_notes.md").write_text("Chapter 01 content.")
        (tmp_path / "chapter_84_notes.md").write_text("Chapter 84 content.")
        (tmp_path / "chapter_99_notes.md").write_text("Chapter 99 content.")

        service = ChapterNotesService(notes_directory=str(tmp_path))

        # Pass unsorted list
        result = service.load_chapter_notes(["99", "01", "84"])

        # Find positions - should be sorted
        pos_01 = result.find("CHAPTER 01")
        pos_84 = result.find("CHAPTER 84")
        pos_99 = result.find("CHAPTER 99")

        assert pos_01 < pos_84 < pos_99, "Chapters should be sorted"

    def test_missing_directory_returns_message(self):
        """Test returns message when notes directory doesn't exist."""
        service = ChapterNotesService(notes_directory="/nonexistent/path")

        result = service.load_chapter_notes(["84"])

        assert result == "Chapter notes not available."

    def test_missing_chapter_file_skipped(self, tmp_path):
        """Test that missing chapter files are skipped gracefully."""
        # Create only one chapter file
        (tmp_path / "chapter_84_notes.md").write_text("Machinery content.")

        service = ChapterNotesService(notes_directory=str(tmp_path))

        # Request both existing and non-existing
        result = service.load_chapter_notes(["84", "99"])

        assert "═══ CHAPTER 84 NOTES ═══" in result
        assert "CHAPTER 99" not in result  # Non-existing skipped

    def test_all_chapters_missing_returns_message(self, tmp_path):
        """Test returns message when all requested chapters are missing."""
        # Create empty directory
        service = ChapterNotesService(notes_directory=str(tmp_path))

        result = service.load_chapter_notes(["99", "98"])

        assert result == "No chapter notes available for the chapters in these paths."

    def test_empty_chapter_list(self, tmp_path):
        """Test handling of empty chapter list."""
        (tmp_path / "chapter_84_notes.md").write_text("Content.")

        service = ChapterNotesService(notes_directory=str(tmp_path))

        result = service.load_chapter_notes([])

        assert result == "No chapter notes available for the chapters in these paths."

    def test_strips_whitespace_from_content(self, tmp_path):
        """Test that whitespace is stripped from file content."""
        notes_file = tmp_path / "chapter_84_notes.md"
        notes_file.write_text("  \n  Content with whitespace.  \n  ")

        service = ChapterNotesService(notes_directory=str(tmp_path))

        result = service.load_chapter_notes(["84"])

        # Content should be stripped
        assert "Content with whitespace." in result
        # Leading/trailing whitespace should be gone from content section
        lines = result.split("\n")
        content_line = [line for line in lines if "Content" in line][0]
        assert content_line == "Content with whitespace."

    def test_notes_separated_by_double_newlines(self, tmp_path):
        """Test that multiple chapter notes are separated by double newlines."""
        (tmp_path / "chapter_01_notes.md").write_text("First chapter.")
        (tmp_path / "chapter_02_notes.md").write_text("Second chapter.")

        service = ChapterNotesService(notes_directory=str(tmp_path))

        result = service.load_chapter_notes(["01", "02"])

        # Should have double newline between chapters
        assert "\n\n" in result
        parts = result.split("\n\n")
        assert len(parts) == 2
        assert "CHAPTER 01" in parts[0]
        assert "CHAPTER 02" in parts[1]


class TestChapterNotesServiceEdgeCases:
    """Edge case tests for ChapterNotesService."""

    def test_chapter_code_with_leading_zeros(self, tmp_path):
        """Test chapter codes with leading zeros."""
        (tmp_path / "chapter_01_notes.md").write_text("Chapter one.")

        service = ChapterNotesService(notes_directory=str(tmp_path))

        result = service.load_chapter_notes(["01"])

        assert "═══ CHAPTER 01 NOTES ═══" in result
        assert "Chapter one." in result

    def test_handles_unicode_content(self, tmp_path):
        """Test handling of unicode characters in notes."""
        (tmp_path / "chapter_84_notes.md").write_text(
            "Máquinas y aparatos mecánicos\n日本語テスト"
        )

        service = ChapterNotesService(notes_directory=str(tmp_path))

        result = service.load_chapter_notes(["84"])

        assert "Máquinas y aparatos mecánicos" in result
        assert "日本語テスト" in result

    def test_preserves_multiline_content(self, tmp_path):
        """Test that multiline content is preserved."""
        content = """# Chapter 84 Notes

## Scope
This chapter covers machinery.

## Exclusions
- Electrical items (Chapter 85)
- Vehicles (Chapter 87)"""
        (tmp_path / "chapter_84_notes.md").write_text(content)

        service = ChapterNotesService(notes_directory=str(tmp_path))

        result = service.load_chapter_notes(["84"])

        assert "# Chapter 84 Notes" in result
        assert "## Scope" in result
        assert "## Exclusions" in result
        assert "- Electrical items (Chapter 85)" in result
