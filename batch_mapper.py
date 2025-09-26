"""Consolidated batch mapping tool for tax code to HS code mapping.

This tool combines all batch mapping functionality into a single script with command-line options.
Replaces: run_100_mapping.py, run_next_100_mapping*.py, and related batch processing scripts.
"""

import asyncio
import json
import argparse
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from tqdm.asyncio import tqdm as async_tqdm

from hs_agent.workflows.tax_code_mapper import TaxCodeMapper, MappingResult, TaxCodeEntry
from hs_agent.client.api_client import HSAgentAPIClient
from hs_agent.config import AgentType


class EnhancedMappingResult:
    """Enhanced mapping result with full classification traces."""

    def __init__(self, basic_result: MappingResult, full_classification_results: Dict[str, Any]):
        # Copy basic result fields
        self.avalara_code = basic_result.avalara_code
        self.avalara_description = basic_result.avalara_description
        self.avalara_additional_info = basic_result.avalara_additional_info
        self.hs_code = basic_result.hs_code
        self.hs_description = basic_result.hs_description
        self.confidence = basic_result.confidence
        self.reasoning = basic_result.reasoning
        self.chapter_code = basic_result.chapter_code
        self.heading_code = basic_result.heading_code
        self.processing_time_ms = basic_result.processing_time_ms
        self.error = basic_result.error

        # Add full classification details
        self.full_classification = full_classification_results

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "avalara_code": self.avalara_code,
            "avalara_description": self.avalara_description,
            "avalara_additional_info": self.avalara_additional_info,
            "hs_code": self.hs_code,
            "hs_description": self.hs_description,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "chapter_code": self.chapter_code,
            "heading_code": self.heading_code,
            "processing_time_ms": self.processing_time_ms,
            "error": self.error,
            "hierarchical_classification": self.full_classification
        }


class EnhancedTaxCodeMapper(TaxCodeMapper):
    """Enhanced tax code mapper that captures full classification details."""

    async def map_single_tax_code_enhanced(self, tax_entry: TaxCodeEntry) -> EnhancedMappingResult:
        """Map a single tax code with full classification details."""
        try:
            start_time = time.time()

            # Use the agent to get full hierarchical classification
            full_result = await self.agent.classify_hierarchical(
                tax_entry.full_description, top_k=5
            )

            processing_time_ms = (time.time() - start_time) * 1000

            # Get HS code description
            hs_code_info = self.hs_loader.get_code_info(full_result["final_code"])
            hs_description = hs_code_info.description if hs_code_info else "Description not available"

            # Create basic result
            basic_result = MappingResult(
                avalara_code=tax_entry.avalara_code,
                avalara_description=tax_entry.description or "",
                avalara_additional_info=tax_entry.additional_info or "",
                hs_code=full_result["final_code"],
                hs_description=hs_description,
                confidence=full_result["overall_confidence"],
                reasoning=f"Hierarchical classification with {full_result['overall_confidence']:.2%} confidence",
                chapter_code=full_result.get("chapter", {}).get("selected_code", "") if "chapter" in full_result else "",
                heading_code=full_result.get("heading", {}).get("selected_code", "") if "heading" in full_result else "",
                processing_time_ms=processing_time_ms
            )

            # Create enhanced result with full details
            return EnhancedMappingResult(basic_result, full_result)

        except Exception as e:
            # Create error result
            error_result = MappingResult(
                avalara_code=tax_entry.avalara_code,
                avalara_description=tax_entry.description or "",
                avalara_additional_info=tax_entry.additional_info or "",
                hs_code="",
                hs_description="",
                confidence=0.0,
                reasoning="",
                chapter_code="",
                heading_code="",
                processing_time_ms=0.0,
                error=str(e)
            )
            return EnhancedMappingResult(error_result, {"error": str(e)})


class BatchMapper:
    """Main batch mapping orchestrator."""

    def __init__(self, data_file: str = "data/avalara_tax_codes.xlsx", confidence_threshold: float = 0.6):
        self.data_file = data_file
        self.confidence_threshold = confidence_threshold
        self.mapper = None

    async def init_mapper(self, use_api: bool = False, agent_type: AgentType = AgentType.LANGGRAPH):
        """Initialize the mapper (local or API-based)."""
        if use_api:
            print("🌐 Using API-based mapping")
            # For API-based mapping, we'll use a different approach
            self.api_client = HSAgentAPIClient()
            self.use_api = True
        else:
            print("🏠 Using local mapping")
            self.mapper = EnhancedTaxCodeMapper(self.data_file, self.confidence_threshold)
            self.use_api = False

    async def map_via_api(self, tax_entry: TaxCodeEntry) -> EnhancedMappingResult:
        """Map using API client."""
        try:
            start_time = time.time()

            result = await self.api_client.classify_product(
                product_description=tax_entry.full_description,
                agent_type=AgentType.LANGGRAPH,
                top_k=5,
                include_reasoning=True
            )

            processing_time_ms = (time.time() - start_time) * 1000

            # Create basic result from API response
            basic_result = MappingResult(
                avalara_code=tax_entry.avalara_code,
                avalara_description=tax_entry.description or "",
                avalara_additional_info=tax_entry.additional_info or "",
                hs_code=result["final_hs_code"],
                hs_description=result["final_description"],
                confidence=result["overall_confidence"],
                reasoning=result.get("reasoning", "API classification"),
                chapter_code="",  # Extract from hierarchical results if available
                heading_code="",  # Extract from hierarchical results if available
                processing_time_ms=processing_time_ms
            )

            # Use API result as full classification
            full_classification = {
                "final_code": result["final_hs_code"],
                "overall_confidence": result["overall_confidence"],
                "api_result": True
            }

            return EnhancedMappingResult(basic_result, full_classification)

        except Exception as e:
            error_result = MappingResult(
                avalara_code=tax_entry.avalara_code,
                avalara_description=tax_entry.description or "",
                avalara_additional_info=tax_entry.additional_info or "",
                hs_code="",
                hs_description="",
                confidence=0.0,
                reasoning="",
                chapter_code="",
                heading_code="",
                processing_time_ms=0.0,
                error=str(e)
            )
            return EnhancedMappingResult(error_result, {"error": str(e)})

    async def run_batch_mapping(self, start_idx: int = 0, count: int = 100,
                               output_prefix: str = "batch_mapping", use_api: bool = False):
        """Run batch mapping on specified range of tax codes."""

        await self.init_mapper(use_api)

        # Load tax codes
        if self.mapper:
            tax_codes = self.mapper.tax_codes[start_idx:start_idx + count]
        else:
            # Load tax codes manually for API mode
            import pandas as pd
            df = pd.read_excel(self.data_file)
            tax_codes = []
            for _, row in df.iloc[start_idx:start_idx + count].iterrows():
                tax_codes.append(TaxCodeEntry(
                    avalara_code=str(row.get('avalara_code', '')),
                    description=str(row.get('description', '')),
                    additional_info=str(row.get('additional_info', ''))
                ))

        print(f"🚀 Starting batch mapping:")
        print(f"   Range: {start_idx} to {start_idx + len(tax_codes) - 1}")
        print(f"   Count: {len(tax_codes)} codes")
        print(f"   Mode: {'API' if use_api else 'Local'}")

        # Process tax codes
        results = []
        successful = 0
        failed = 0

        async for i, tax_entry in async_tqdm(enumerate(tax_codes), total=len(tax_codes), desc="Processing"):
            try:
                if self.use_api:
                    result = await self.map_via_api(tax_entry)
                else:
                    result = await self.mapper.map_single_tax_code_enhanced(tax_entry)

                results.append(result)

                if result.error:
                    failed += 1
                    print(f"❌ Failed {tax_entry.avalara_code}: {result.error}")
                else:
                    successful += 1
                    if i < 5:  # Show first 5 results
                        print(f"✅ {result.avalara_code} → {result.hs_code} ({result.confidence:.2%})")

            except Exception as e:
                failed += 1
                print(f"❌ Exception for {tax_entry.avalara_code}: {e}")
                # Create error result
                error_result = MappingResult(
                    avalara_code=tax_entry.avalara_code,
                    avalara_description=tax_entry.description or "",
                    avalara_additional_info=tax_entry.additional_info or "",
                    hs_code="",
                    hs_description="",
                    confidence=0.0,
                    reasoning="",
                    chapter_code="",
                    heading_code="",
                    processing_time_ms=0.0,
                    error=str(e)
                )
                results.append(EnhancedMappingResult(error_result, {"error": str(e)}))

        # Generate output filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"{output_prefix}_{start_idx}_{start_idx + count - 1}_{timestamp}.json"

        # Create output data
        output_data = {
            "metadata": {
                "total_processed": len(results),
                "successful_mappings": successful,
                "failed_mappings": failed,
                "success_rate": successful / len(results) if results else 0.0,
                "confidence_threshold": self.confidence_threshold,
                "processing_timestamp": datetime.now().isoformat(),
                "start_index": start_idx,
                "end_index": start_idx + len(tax_codes) - 1,
                "data_file": self.data_file,
                "mode": "API" if use_api else "Local",
                "description": f"Batch mapping of {len(tax_codes)} tax codes (indices {start_idx}-{start_idx + len(tax_codes) - 1})"
            },
            "mappings": [result.to_dict() for result in results]
        }

        # Save results
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        # Print summary
        print(f"\n📊 BATCH MAPPING SUMMARY:")
        print(f"   Total processed: {len(results)}")
        print(f"   Successful: {successful} ({successful/len(results)*100:.1f}%)")
        print(f"   Failed: {failed} ({failed/len(results)*100:.1f}%)")
        print(f"   Output file: {output_file}")

        return output_file

    async def quick_test(self, count: int = 1):
        """Run a quick test with specified number of tax codes."""
        await self.init_mapper()

        tax_codes = self.mapper.tax_codes[:count]
        print(f"🧪 Quick test with {count} tax code(s):")

        for i, tax_entry in enumerate(tax_codes):
            print(f"\n{i+1}. Testing: {tax_entry.avalara_code}")
            print(f"   Description: {tax_entry.full_description[:100]}...")

            result = await self.mapper.map_single_tax_code_enhanced(tax_entry)

            print(f"   Result: {result.hs_code}")
            print(f"   HS Description: {result.hs_description[:80]}...")
            print(f"   Confidence: {result.confidence:.3f}")


async def main():
    parser = argparse.ArgumentParser(description="HS Agent Batch Mapping Tool")
    parser.add_argument('command', choices=['batch', 'test'],
                       help='Command to run')
    parser.add_argument('--start', type=int, default=0,
                       help='Starting index (default: 0)')
    parser.add_argument('--count', type=int, default=100,
                       help='Number of codes to process (default: 100)')
    parser.add_argument('--confidence', type=float, default=0.6,
                       help='Confidence threshold (default: 0.6)')
    parser.add_argument('--data-file', default='data/avalara_tax_codes.xlsx',
                       help='Tax codes data file (default: data/avalara_tax_codes.xlsx)')
    parser.add_argument('--output-prefix', default='batch_mapping',
                       help='Output file prefix (default: batch_mapping)')
    parser.add_argument('--api', action='store_true',
                       help='Use API mode instead of local agents')

    args = parser.parse_args()

    batch_mapper = BatchMapper(args.data_file, args.confidence)

    if args.command == 'batch':
        await batch_mapper.run_batch_mapping(
            start_idx=args.start,
            count=args.count,
            output_prefix=args.output_prefix,
            use_api=args.api
        )
    elif args.command == 'test':
        await batch_mapper.quick_test(args.count)


if __name__ == "__main__":
    asyncio.run(main())