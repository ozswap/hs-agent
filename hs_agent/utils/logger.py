"""Centralized logging utility with consistent styling."""

import logging
from typing import Optional
from rich.logging import RichHandler
from rich.console import Console

# Initialize rich console
console = Console()

# Color scheme - DRY principle
class LogColors:
    """Centralized color definitions for consistent logging."""

    # Status colors
    SUCCESS = "bold green"
    ERROR = "bold red"
    WARNING = "bold yellow"
    INFO = "bold cyan"

    # Emphasis colors
    HIGHLIGHT = "bold magenta"
    ACCENT = "yellow"
    PRODUCT = "cyan"
    CODE = "bold magenta"

    # Dim/secondary
    DIM = "dim"

    # Emojis
    ROCKET = "🚀"
    CHECK = "✅"
    CROSS = "❌"
    PACKAGE = "📦"
    TARGET = "🎯"
    SPARKLES = "✨"
    GLOBE = "🌐"
    CHART = "📊"
    NOTES = "📋"
    THINKING = "🤔"
    LIGHTNING = "⚡"


class HSLogger:
    """Custom logger with rich formatting and consistent styling."""

    def __init__(self, name: str):
        """Initialize logger with rich handler."""
        self.logger = logging.getLogger(name)

        # Only add handler if not already present
        if not self.logger.handlers:
            self.logger.setLevel(logging.INFO)
            handler = RichHandler(
                console=console,
                rich_tracebacks=True,
                markup=True,
                show_time=True,
                show_path=False
            )
            handler.setFormatter(logging.Formatter("%(message)s"))
            self.logger.addHandler(handler)
            self.logger.propagate = False

    def _format_text(self, text: str, color: str) -> str:
        """Format text with color markup."""
        return f"[{color}]{text}[/{color}]"

    # Core logging methods
    def info(self, message: str):
        """Log info message."""
        self.logger.info(message)

    def error(self, message: str):
        """Log error message."""
        self.logger.error(message)

    def warning(self, message: str):
        """Log warning message."""
        self.logger.warning(message)

    def debug(self, message: str):
        """Log debug message."""
        self.logger.debug(message)

    # Specialized logging methods for common patterns
    def init_start(self, component: str, details: Optional[str] = None):
        """Log initialization start."""
        msg = f"{LogColors.ROCKET} {self._format_text('Initializing', LogColors.INFO)} {self._format_text(component, LogColors.HIGHLIGHT)}"
        if details:
            msg += f" {self._format_text(f'({details})', LogColors.DIM)}"
        self.logger.info(msg + "...")

    def init_complete(self, component: str, details: Optional[str] = None):
        """Log initialization complete."""
        msg = f"{LogColors.CHECK} {self._format_text(component, LogColors.SUCCESS)} ready!"
        if details:
            msg += f" {self._format_text(details, LogColors.DIM)}"
        self.logger.info(msg)

    def classify_start(self, product: str, params: Optional[dict] = None):
        """Log classification start."""
        msg = f"{LogColors.PACKAGE} {self._format_text('Classifying:', 'bold')} {self._format_text(product, LogColors.PRODUCT)}"
        if params:
            param_str = ", ".join(f"{k}={v}" for k, v in params.items())
            msg += f" {self._format_text(f'({param_str})', LogColors.DIM)}"
        self.logger.info(msg)

    def classify_result(self, code: str, confidence: float, extra: Optional[str] = None):
        """Log classification result."""
        msg = f"{LogColors.TARGET} {self._format_text('Result:', LogColors.SUCCESS)} {self._format_text(code, LogColors.CODE)}"
        msg += f" {self._format_text(f'(confidence: {confidence:.2%})', LogColors.DIM)}"
        if extra:
            msg += f" {self._format_text(extra, LogColors.ACCENT)}"
        self.logger.info(msg)

    def wide_net_start(self, product: str, top_k: int, max_selections: int):
        """Log wide net classification start."""
        msg = f"{LogColors.GLOBE} {self._format_text('Wide Net Classification:', 'bold')} {self._format_text(product, LogColors.PRODUCT)}"
        msg += f" {self._format_text(f'(top_k={top_k}, max_selections={max_selections})', LogColors.DIM)}"
        self.logger.info(msg)

    def wide_net_result(self, paths_count: int, final_code: str, confidence: float):
        """Log wide net classification result."""
        msg = f"{LogColors.SPARKLES} {self._format_text('Wide Net Result:', LogColors.SUCCESS)}"
        msg += f" Explored {self._format_text(str(paths_count), LogColors.ACCENT)} path(s)"
        msg += f" → Final: {self._format_text(final_code, LogColors.CODE)}"
        msg += f" {self._format_text(f'(confidence: {confidence:.2%})', LogColors.DIM)}"
        self.logger.info(msg)

    def loading_data(self, data_type: str, count: int):
        """Log data loading."""
        msg = f"{LogColors.CHART} Loaded {self._format_text(str(count), LogColors.ACCENT)} {data_type}"
        self.logger.info(msg)

    def error_msg(self, operation: str, error: Exception):
        """Log error with operation context."""
        msg = f"{LogColors.CROSS} {self._format_text(f'{operation} failed:', LogColors.ERROR)} {error}"
        self.logger.error(msg)

    def chapter_notes_loaded(self, chapter_codes: list):
        """Log chapter notes loading."""
        chapters_str = ", ".join(chapter_codes)
        msg = f"{LogColors.NOTES} Loaded chapter notes for: {self._format_text(chapters_str, LogColors.ACCENT)}"
        self.logger.info(msg)

    def step_start(self, step_name: str, details: Optional[str] = None):
        """Log workflow step start."""
        msg = f"{LogColors.LIGHTNING} {self._format_text(step_name, 'bold')}"
        if details:
            msg += f" {self._format_text(f'({details})', LogColors.DIM)}"
        self.logger.info(msg)


# Global logger instances (singleton pattern)
_loggers = {}


def get_logger(name: str) -> HSLogger:
    """Get or create a logger instance."""
    if name not in _loggers:
        _loggers[name] = HSLogger(name)
    return _loggers[name]
