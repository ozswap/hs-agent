"""Domain entity models for HS Agent.

This module defines the core domain entities used throughout the system,
such as HS codes, tax codes, and product examples.
"""

from typing import List, Optional
from pydantic import BaseModel, Field, validator
from pathlib import Path


class HSCode(BaseModel):
    """Represents an HS code with its metadata.
    
    This is the core entity representing a Harmonized System code
    with all its associated information and hierarchy.
    """
    
    code: str = Field(
        ...,
        description="The HS code (e.g., '84', '8471', '847130')",
        min_length=2,
        max_length=10
    )
    
    description: str = Field(
        ...,
        description="Human-readable description of the HS code",
        min_length=1
    )
    
    level: int = Field(
        ...,
        description="The digit level of the code (2, 4, or 6)",
        ge=2,
        le=6
    )
    
    parent: Optional[str] = Field(
        None,
        description="Parent code for hierarchical navigation"
    )
    
    section: Optional[str] = Field(
        None,
        description="Section identifier for grouping"
    )
    
    category: Optional[str] = Field(
        None,
        description="Category classification"
    )
    
    @validator("code")
    def validate_code_format(cls, v):
        """Validate HS code format."""
        if not v.isdigit():
            raise ValueError("HS code must contain only digits")
        return v
    
    @validator("level")
    def validate_level_consistency(cls, v, values):
        """Validate that level matches code length."""
        if "code" in values:
            code_length = len(values["code"])
            if v != code_length:
                raise ValueError(f"Level {v} doesn't match code length {code_length}")
        return v
    
    @property
    def is_chapter(self) -> bool:
        """Check if this is a 2-digit chapter code."""
        return self.level == 2
    
    @property
    def is_heading(self) -> bool:
        """Check if this is a 4-digit heading code."""
        return self.level == 4
    
    @property
    def is_subheading(self) -> bool:
        """Check if this is a 6-digit subheading code."""
        return self.level == 6
    
    @property
    def chapter_code(self) -> str:
        """Get the 2-digit chapter code."""
        return self.code[:2]
    
    @property
    def heading_code(self) -> str:
        """Get the 4-digit heading code."""
        return self.code[:4] if len(self.code) >= 4 else self.code
    
    def __str__(self) -> str:
        return f"{self.code}: {self.description}"


class TaxCodeEntry(BaseModel):
    """Represents an Avalara tax code entry for mapping to HS codes.
    
    This entity represents a tax code that needs to be mapped to
    an appropriate HS code through the classification process.
    """
    
    avalara_code: str = Field(
        ...,
        description="Avalara tax code identifier",
        min_length=1
    )
    
    description: str = Field(
        ...,
        description="Description of the tax code",
        min_length=1
    )
    
    additional_info: Optional[str] = Field(
        None,
        description="Additional information about the tax code"
    )
    
    category: Optional[str] = Field(
        None,
        description="Tax code category"
    )
    
    @property
    def combined_description(self) -> str:
        """Get combined description including additional info."""
        if self.additional_info:
            return f"{self.description}. {self.additional_info}"
        return self.description
    
    def __str__(self) -> str:
        return f"{self.avalara_code}: {self.description}"


class ProductExample(BaseModel):
    """Represents a product example for HS code classification.
    
    This entity represents real-world product examples that are
    associated with specific HS codes for training and validation.
    """
    
    hs_code: str = Field(
        ...,
        description="Associated HS code",
        min_length=6,
        max_length=6
    )
    
    product_description: str = Field(
        ...,
        description="Product description",
        min_length=1
    )
    
    source: Optional[str] = Field(
        None,
        description="Source of the example (e.g., 'training_data', 'user_input')"
    )
    
    confidence: Optional[float] = Field(
        None,
        description="Confidence in the HS code assignment",
        ge=0.0,
        le=1.0
    )
    
    @validator("hs_code")
    def validate_hs_code(cls, v):
        """Validate HS code format."""
        if not v.isdigit():
            raise ValueError("HS code must contain only digits")
        return v
    
    def __str__(self) -> str:
        return f"{self.hs_code}: {self.product_description[:50]}..."


class DataFile(BaseModel):
    """Represents a data file with metadata.
    
    This entity represents data files used by the system,
    with validation and metadata tracking.
    """
    
    path: Path = Field(
        ...,
        description="Path to the data file"
    )
    
    file_type: str = Field(
        ...,
        description="Type of file (e.g., 'csv', 'xlsx', 'json')"
    )
    
    description: str = Field(
        ...,
        description="Description of the file contents"
    )
    
    record_count: Optional[int] = Field(
        None,
        description="Number of records in the file",
        ge=0
    )
    
    last_modified: Optional[str] = Field(
        None,
        description="Last modification timestamp"
    )
    
    @validator("path")
    def validate_file_exists(cls, v):
        """Validate that the file exists."""
        if not v.exists():
            raise ValueError(f"File does not exist: {v}")
        return v
    
    @validator("file_type")
    def validate_file_type(cls, v, values):
        """Validate file type matches extension."""
        if "path" in values:
            path = values["path"]
            expected_extension = f".{v}"
            if not str(path).endswith(expected_extension):
                raise ValueError(f"File type {v} doesn't match file extension")
        return v
    
    def __str__(self) -> str:
        return f"{self.file_type.upper()} file: {self.path}"