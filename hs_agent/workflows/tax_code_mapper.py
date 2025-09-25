"""Tax Code to HS Code Mapping Service."""

import os
import json
import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import pandas as pd
from tqdm.asyncio import tqdm_asyncio

from hs_agent.core.data_loader import HSDataLoader
from hs_agent.agents.langgraph.agents import HSLangGraphAgent


@dataclass
class TaxCodeEntry:
    """Represents a single Avalara tax code entry."""
    avalara_code: str
    description: str
    additional_info: str

    @property
    def full_description(self) -> str:
        """Combine description and additional info for HS classification."""
        if pd.isna(self.additional_info) or not self.additional_info:
            return self.description or ""

        if pd.isna(self.description) or not self.description:
            return self.additional_info or ""

        return f"{self.description}. {self.additional_info}"


@dataclass
class MappingResult:
    """Represents a tax code to HS code mapping result."""
    avalara_code: str
    avalara_description: str
    avalara_additional_info: str
    hs_code: str
    hs_description: str
    confidence: float
    reasoning: str
    chapter_code: str
    heading_code: str
    processing_time_ms: float
    error: Optional[str] = None


class TaxCodeMapper:
    """Service to map Avalara tax codes to HS codes using the classification agent."""

    def __init__(self, excel_path: str, confidence_threshold: float = 0.7):
        self.excel_path = excel_path
        self.confidence_threshold = confidence_threshold

        # Initialize HS data loader and agent
        self.data_loader = HSDataLoader()
        self.data_loader.load_all_data()  # Load the HS codes data
        self.hs_agent = HSLangGraphAgent(self.data_loader)

        # Load tax codes from Excel
        self.tax_codes = self._load_tax_codes()

    def _load_tax_codes(self) -> List[TaxCodeEntry]:
        """Load and clean tax codes from Excel file."""
        print(f"📊 Loading tax codes from {self.excel_path}...")

        # Read Excel with proper column names
        df = pd.read_excel(self.excel_path, header=0)
        df.columns = ['AvaTax_System_Tax_Code', 'AvaTax_System_Tax_Code_Description', 'Additional_AvaTax_System_Tax_Code_Information']

        # Remove header row and empty entries
        df = df[df['AvaTax_System_Tax_Code'] != 'AvaTax System Tax Code']
        df = df.dropna(subset=['AvaTax_System_Tax_Code'])

        # Convert to TaxCodeEntry objects
        tax_codes = []
        for _, row in df.iterrows():
            entry = TaxCodeEntry(
                avalara_code=str(row['AvaTax_System_Tax_Code']),
                description=row['AvaTax_System_Tax_Code_Description'] if pd.notna(row['AvaTax_System_Tax_Code_Description']) else "",
                additional_info=row['Additional_AvaTax_System_Tax_Code_Information'] if pd.notna(row['Additional_AvaTax_System_Tax_Code_Information']) else ""
            )

            # Only include entries with meaningful descriptions
            if entry.full_description.strip():
                tax_codes.append(entry)

        print(f"✅ Loaded {len(tax_codes)} valid tax code entries")
        return tax_codes

    async def map_single_tax_code(self, tax_entry: TaxCodeEntry) -> MappingResult:
        """Map a single tax code to HS code."""
        start_time = datetime.now()

        try:
            # Use the full description for HS classification
            product_description = tax_entry.full_description

            # Classify using the LangGraph agent
            results = await self.hs_agent.classify_hierarchical(
                product_description=product_description,
                top_k=5
            )

            processing_time = (datetime.now() - start_time).total_seconds() * 1000

            # Extract final results
            final_hs_code = results["final_code"]
            overall_confidence = results["overall_confidence"]

            # Get HS code description (remove dots for lookup)
            hs_code_clean = final_hs_code.replace(".", "")
            hs_code_obj = self.data_loader.codes_6digit.get(hs_code_clean)
            hs_description = hs_code_obj.description if hs_code_obj else "Description not found"

            # Get reasoning from subheading result
            reasoning = results["subheading"].reasoning if results.get("subheading") else "No detailed reasoning available"

            return MappingResult(
                avalara_code=tax_entry.avalara_code,
                avalara_description=tax_entry.description,
                avalara_additional_info=tax_entry.additional_info,
                hs_code=final_hs_code,
                hs_description=hs_description,
                confidence=overall_confidence,
                reasoning=reasoning,
                chapter_code=results["chapter"].selected_code if results.get("chapter") else "",
                heading_code=results["heading"].selected_code if results.get("heading") else "",
                processing_time_ms=processing_time
            )

        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            print(f"❌ Error processing {tax_entry.avalara_code}: {e}")

            return MappingResult(
                avalara_code=tax_entry.avalara_code,
                avalara_description=tax_entry.description,
                avalara_additional_info=tax_entry.additional_info,
                hs_code="",
                hs_description="",
                confidence=0.0,
                reasoning="",
                chapter_code="",
                heading_code="",
                processing_time_ms=processing_time,
                error=str(e)
            )

    async def map_batch(self, batch_size: int = 10, max_items: Optional[int] = None) -> List[MappingResult]:
        """Map multiple tax codes to HS codes in batches."""

        # Limit items if specified
        items_to_process = self.tax_codes[:max_items] if max_items else self.tax_codes

        print(f"🚀 Starting batch mapping of {len(items_to_process)} tax codes...")
        print(f"📊 Confidence threshold: {self.confidence_threshold}")
        print(f"⚡ Batch size: {batch_size}")

        results = []

        # Process in batches with progress tracking
        for i in tqdm_asyncio(range(0, len(items_to_process), batch_size), desc="Processing batches"):
            batch = items_to_process[i:i + batch_size]

            # Process batch concurrently
            batch_tasks = [self.map_single_tax_code(entry) for entry in batch]
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)

            # Handle any exceptions
            for j, result in enumerate(batch_results):
                if isinstance(result, Exception):
                    error_result = MappingResult(
                        avalara_code=batch[j].avalara_code,
                        avalara_description=batch[j].description,
                        avalara_additional_info=batch[j].additional_info,
                        hs_code="",
                        hs_description="",
                        confidence=0.0,
                        reasoning="",
                        chapter_code="",
                        heading_code="",
                        processing_time_ms=0.0,
                        error=str(result)
                    )
                    results.append(error_result)
                else:
                    results.append(result)

        return results

    def save_results(self, results: List[MappingResult], output_path: str = None) -> str:
        """Save mapping results to JSON and CSV files."""

        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"tax_to_hs_mapping_{timestamp}"

        # Convert to dictionaries for JSON serialization
        results_data = []
        high_confidence_results = []

        for result in results:
            result_dict = {
                "avalara_code": result.avalara_code,
                "avalara_description": result.avalara_description,
                "avalara_additional_info": result.avalara_additional_info,
                "hs_code": result.hs_code,
                "hs_description": result.hs_description,
                "confidence": result.confidence,
                "reasoning": result.reasoning,
                "chapter_code": result.chapter_code,
                "heading_code": result.heading_code,
                "processing_time_ms": result.processing_time_ms,
                "error": result.error
            }

            results_data.append(result_dict)

            # Filter high confidence results
            if result.confidence >= self.confidence_threshold and not result.error:
                high_confidence_results.append(result_dict)

        # Save all results as JSON
        json_path = f"{output_path}_all.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump({
                "metadata": {
                    "total_processed": len(results),
                    "high_confidence_count": len(high_confidence_results),
                    "confidence_threshold": self.confidence_threshold,
                    "processing_timestamp": datetime.now().isoformat()
                },
                "results": results_data
            }, f, indent=2, ensure_ascii=False)

        # Save high confidence results as CSV for easy review
        if high_confidence_results:
            csv_path = f"{output_path}_high_confidence.csv"
            df = pd.DataFrame(high_confidence_results)
            df.to_csv(csv_path, index=False, encoding='utf-8')

            print(f"✅ Saved {len(high_confidence_results)} high-confidence mappings to {csv_path}")

        # Print summary statistics
        successful_mappings = len([r for r in results if not r.error])
        avg_confidence = sum(r.confidence for r in results if not r.error) / max(successful_mappings, 1)

        print(f"\n📊 MAPPING SUMMARY:")
        print(f"   Total processed: {len(results)}")
        print(f"   Successful: {successful_mappings}")
        print(f"   Failed: {len(results) - successful_mappings}")
        print(f"   High confidence (≥{self.confidence_threshold}): {len(high_confidence_results)}")
        print(f"   Average confidence: {avg_confidence:.3f}")
        print(f"   Results saved to: {json_path}")

        return json_path


# Convenience function for quick testing
async def test_mapping_sample():
    """Test the mapping with a small sample of tax codes."""
    mapper = TaxCodeMapper("data/avalara_tax_codes.xlsx", confidence_threshold=0.7)

    # Map first 5 tax codes as a test
    results = await mapper.map_batch(batch_size=2, max_items=5)

    # Save results
    output_path = mapper.save_results(results, "test_mapping")

    print(f"\n🎉 Test mapping completed! Check {output_path}")

    return results


if __name__ == "__main__":
    # Run test mapping
    asyncio.run(test_mapping_sample())