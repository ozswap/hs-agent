"""Enhanced HS codes data loader with centralized configuration and error handling.

This module provides functionality to load HS (Harmonized System) codes from CSV files
and organize them hierarchically for efficient search and classification operations.
"""

import pandas as pd
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from functools import lru_cache

from hs_agent.config import settings
from hs_agent.core.exceptions import DataLoadingError, ConfigurationError
from hs_agent.core.logging import get_logger
from hs_agent.core.models.entities import HSCode, ProductExample

logger = get_logger(__name__)


class HSDataLoader:
    """Enhanced HS codes data loader with caching and error handling.

    This class provides functionality to load HS (Harmonized System) codes from CSV files
    and organize them hierarchically for efficient search and classification operations.

    Features:
    - Centralized configuration management
    - Comprehensive error handling
    - Data validation and integrity checks
    - Performance monitoring and logging
    - Caching for improved performance

    Examples:
    --------
    >>> loader = HSDataLoader()
    >>> loader.load_all_data()
    >>> print(f"Loaded {len(loader.codes_6digit)} 6-digit codes")
    Loaded 5613 6-digit codes

    >>> codes_2digit = loader.get_codes_by_level(2)
    >>> print(f"Available chapters: {len(codes_2digit)}")
    Available chapters: 97
    """

    def __init__(self):
        """Initialize the data loader with configuration from settings."""
        self.data_dir = settings.data_directory
        self.hs_codes_file = settings.hs_codes_file
        self.examples_file = settings.examples_file
        
        # Data storage
        self.codes_2digit: Dict[str, HSCode] = {}
        self.codes_4digit: Dict[str, HSCode] = {}
        self.codes_6digit: Dict[str, HSCode] = {}
        self.examples: Dict[str, List[str]] = {}
        
        # Loading state
        self._data_loaded = False
        self._loading_time_ms: Optional[float] = None
        
        logger.info(
            "📊 HSDataLoader initialized",
            data_dir=str(self.data_dir),
            hs_codes_file=self.hs_codes_file,
            examples_file=self.examples_file
        )

    def load_all_data(self) -> None:
        """Load all HS codes data from CSV files with comprehensive error handling."""
        if self._data_loaded and settings.enable_caching:
            logger.debug("Data already loaded, skipping reload")
            return

        start_time = time.time()
        
        try:
            logger.info("🔄 Starting HS codes data loading")
            
            # Validate data directory and files exist
            self._validate_data_files()
            
            # Load hierarchical codes
            self._load_hierarchical_codes()
            
            # Load product examples
            self._load_examples()
            
            # Validate loaded data
            self._validate_loaded_data()
            
            # Calculate loading time
            self._loading_time_ms = (time.time() - start_time) * 1000
            self._data_loaded = True
            
            # Log success
            total_codes = len(self.codes_2digit) + len(self.codes_4digit) + len(self.codes_6digit)
            total_examples = sum(len(examples) for examples in self.examples.values())
            
            logger.info(
                "✅ HS codes data loaded successfully",
                total_codes=total_codes,
                chapters=len(self.codes_2digit),
                headings=len(self.codes_4digit),
                subheadings=len(self.codes_6digit),
                examples=total_examples,
                loading_time_ms=self._loading_time_ms
            )
            
        except Exception as e:
            error_msg = f"Failed to load HS codes data: {str(e)}"
            logger.error(error_msg, error_type=type(e).__name__)
            raise DataLoadingError(
                message=error_msg,
                error_code="DATA_LOADING_FAILED",
                details={
                    "data_dir": str(self.data_dir),
                    "hs_codes_file": self.hs_codes_file,
                    "examples_file": self.examples_file,
                    "original_error": str(e)
                },
                cause=e
            )

    def _validate_data_files(self) -> None:
        """Validate that required data files exist and are readable."""
        hs_codes_path = self.data_dir / self.hs_codes_file
        examples_path = self.data_dir / self.examples_file
        
        if not self.data_dir.exists():
            raise ConfigurationError(
                message=f"Data directory does not exist: {self.data_dir}",
                error_code="DATA_DIRECTORY_NOT_FOUND",
                details={"data_dir": str(self.data_dir)}
            )
        
        if not hs_codes_path.exists():
            raise DataLoadingError(
                message=f"HS codes file not found: {hs_codes_path}",
                error_code="HS_CODES_FILE_NOT_FOUND",
                details={"file_path": str(hs_codes_path)}
            )
        
        if not examples_path.exists():
            logger.warning(
                f"Examples file not found: {examples_path}. Examples will not be available.",
                file_path=str(examples_path)
            )

    def _load_hierarchical_codes(self) -> None:
        """Load hierarchical HS codes from CSV file."""
        hs_codes_path = self.data_dir / self.hs_codes_file
        
        try:
            logger.debug(f"Loading HS codes from {hs_codes_path}")
            df = pd.read_csv(hs_codes_path)
            
            # Validate required columns
            required_columns = ['hscode', 'description', 'level']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise DataLoadingError(
                    message=f"Missing required columns in HS codes file: {missing_columns}",
                    error_code="MISSING_COLUMNS",
                    details={
                        "file_path": str(hs_codes_path),
                        "missing_columns": missing_columns,
                        "available_columns": list(df.columns)
                    }
                )
            
            # Process each row
            for index, row in df.iterrows():
                try:
                    # Validate HS code format before creating HSCode entity
                    hs_code_raw = str(row['hscode']).strip()
                    
                    # Skip rows with invalid HS codes
                    if not hs_code_raw or not hs_code_raw.isdigit() or len(hs_code_raw) < 2:
                        logger.warning(
                            f"Skipping invalid HS code at row {index}: '{hs_code_raw}'",
                            row_index=index,
                            invalid_code=hs_code_raw
                        )
                        continue
                    
                    # Create HSCode entity with validation
                    hs_code = HSCode(
                        code=hs_code_raw,
                        description=str(row['description']),
                        level=int(row['level']),
                        parent=str(row['parent']) if pd.notna(row.get('parent')) else None,
                        section=str(row['section']) if pd.notna(row.get('section')) else None
                    )
                    
                    # Store in appropriate dictionary
                    if hs_code.level == 2:
                        self.codes_2digit[hs_code.code] = hs_code
                    elif hs_code.level == 4:
                        self.codes_4digit[hs_code.code] = hs_code
                    elif hs_code.level == 6:
                        self.codes_6digit[hs_code.code] = hs_code
                    else:
                        logger.warning(
                            f"Invalid HS code level: {hs_code.level} for code {hs_code.code}",
                            code=hs_code.code,
                            level=hs_code.level,
                            row_index=index
                        )
                        
                except Exception as e:
                    logger.warning(
                        f"Failed to process HS code at row {index}: {str(e)}",
                        row_index=index,
                        error=str(e)
                    )
                    continue
                    
        except pd.errors.EmptyDataError:
            raise DataLoadingError(
                message=f"HS codes file is empty: {hs_codes_path}",
                error_code="EMPTY_FILE",
                details={"file_path": str(hs_codes_path)}
            )
        except pd.errors.ParserError as e:
            raise DataLoadingError(
                message=f"Failed to parse HS codes CSV file: {str(e)}",
                error_code="CSV_PARSE_ERROR",
                details={
                    "file_path": str(hs_codes_path),
                    "parser_error": str(e)
                },
                cause=e
            )

    def _load_examples(self) -> None:
        """Load product examples from CSV file."""
        examples_path = self.data_dir / self.examples_file
        
        if not examples_path.exists():
            logger.info("Examples file not found, skipping examples loading")
            return
        
        try:
            logger.debug(f"Loading product examples from {examples_path}")
            df = pd.read_csv(examples_path)
            
            # Validate required columns
            required_columns = ['hs6_code', 'product_description']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                logger.warning(
                    f"Missing columns in examples file: {missing_columns}. Skipping examples.",
                    missing_columns=missing_columns
                )
                return
            
            # Process each row
            for index, row in df.iterrows():
                try:
                    code = str(row['hs6_code'])
                    description = str(row['product_description'])
                    
                    if code not in self.examples:
                        self.examples[code] = []
                    self.examples[code].append(description)
                    
                except Exception as e:
                    logger.warning(
                        f"Failed to process example at row {index}: {str(e)}",
                        row_index=index,
                        error=str(e)
                    )
                    continue
                    
        except Exception as e:
            logger.warning(
                f"Failed to load examples file: {str(e)}. Examples will not be available.",
                file_path=str(examples_path),
                error=str(e)
            )

    def _validate_loaded_data(self) -> None:
        """Validate the integrity of loaded data."""
        # Check minimum data requirements
        if len(self.codes_2digit) == 0:
            raise DataLoadingError(
                message="No 2-digit HS codes loaded",
                error_code="NO_CHAPTER_CODES",
                details={"codes_loaded": 0}
            )
        
        if len(self.codes_6digit) == 0:
            raise DataLoadingError(
                message="No 6-digit HS codes loaded",
                error_code="NO_SUBHEADING_CODES",
                details={"codes_loaded": 0}
            )
        
        # Validate hierarchical consistency
        orphaned_codes = []
        for code, hs_code in self.codes_4digit.items():
            if hs_code.parent and hs_code.parent not in self.codes_2digit:
                orphaned_codes.append(code)
        
        if orphaned_codes:
            logger.warning(
                f"Found {len(orphaned_codes)} 4-digit codes with missing parent chapters",
                orphaned_count=len(orphaned_codes),
                sample_orphaned=orphaned_codes[:5]
            )
        
        # Log data statistics
        logger.debug(
            "Data validation complete",
            chapters=len(self.codes_2digit),
            headings=len(self.codes_4digit),
            subheadings=len(self.codes_6digit),
            examples_codes=len(self.examples),
            orphaned_headings=len(orphaned_codes)
        )

    @lru_cache(maxsize=128)
    def get_codes_by_level(self, level: int) -> Dict[str, HSCode]:
        """Get all codes for a specific level (2, 4, or 6) with caching.
        
        Args:
            level: The HS code level (2, 4, or 6)
            
        Returns:
            Dictionary mapping HS codes to HSCode objects
            
        Raises:
            ValidationError: If level is not 2, 4, or 6
            DataLoadingError: If data is not loaded
        """
        if not self._data_loaded:
            raise DataLoadingError(
                message="Data not loaded. Call load_all_data() first.",
                error_code="DATA_NOT_LOADED"
            )
        
        if level == 2:
            return self.codes_2digit
        elif level == 4:
            return self.codes_4digit
        elif level == 6:
            return self.codes_6digit
        else:
            from hs_agent.core.exceptions import ValidationError
            raise ValidationError(
                message=f"Invalid HS code level: {level}",
                error_code="INVALID_LEVEL",
                details={
                    "provided_level": level,
                    "valid_levels": [2, 4, 6]
                }
            )

    def get_parent_codes(self, code: str, target_level: int) -> List[str]:
        """Get parent codes for a given code at target level.
        
        Args:
            code: The HS code to find parents for
            target_level: The target level for parent codes
            
        Returns:
            List of parent codes at the target level
        """
        if target_level == 2:
            return [code[:2]] if len(code) >= 2 else []
        elif target_level == 4:
            return [code[:4]] if len(code) >= 4 else []
        elif target_level == 6:
            return [code[:6]] if len(code) >= 6 else []
        else:
            from hs_agent.core.exceptions import ValidationError
            raise ValidationError(
                message=f"Invalid target level: {target_level}",
                error_code="INVALID_TARGET_LEVEL",
                details={
                    "provided_level": target_level,
                    "valid_levels": [2, 4, 6]
                }
            )

    def get_examples_for_code(self, code: str) -> List[str]:
        """Get product examples for a specific 6-digit HS code.
        
        Args:
            code: The 6-digit HS code
            
        Returns:
            List of product description examples
        """
        return self.examples.get(code, [])

    def get_code_info(self, code: str) -> Optional[HSCode]:
        """Get detailed information for a specific HS code.
        
        Args:
            code: The HS code to look up
            
        Returns:
            HSCode object if found, None otherwise
        """
        # Try to find the code in appropriate level dictionary
        if len(code) == 2:
            return self.codes_2digit.get(code)
        elif len(code) == 4:
            return self.codes_4digit.get(code)
        elif len(code) == 6:
            return self.codes_6digit.get(code)
        else:
            return None

    @property
    def is_loaded(self) -> bool:
        """Check if data has been loaded."""
        return self._data_loaded

    @property
    def loading_time_ms(self) -> Optional[float]:
        """Get the data loading time in milliseconds."""
        return self._loading_time_ms

    @property
    def data_statistics(self) -> Dict[str, int]:
        """Get statistics about loaded data."""
        return {
            "chapters": len(self.codes_2digit),
            "headings": len(self.codes_4digit),
            "subheadings": len(self.codes_6digit),
            "examples_codes": len(self.examples),
            "total_examples": sum(len(examples) for examples in self.examples.values())
        }

    def __str__(self) -> str:
        """String representation of the data loader."""
        if self._data_loaded:
            stats = self.data_statistics
            return (
                f"HSDataLoader(loaded={self._data_loaded}, "
                f"chapters={stats['chapters']}, "
                f"headings={stats['headings']}, "
                f"subheadings={stats['subheadings']})"
            )
        else:
            return f"HSDataLoader(loaded={self._data_loaded})"