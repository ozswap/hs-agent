"""Main HS classifier orchestrator."""

import asyncio
import os
from pathlib import Path
from typing import Optional, Dict, Any
from langfuse import get_client

from hs_agent.core.data_loader import HSDataLoader
from hs_agent.agents.traditional.agents import HSClassificationAgent
from hs_agent.core.models import FinalClassification, ClassificationResult


class HSClassifier:
    """Main HS code classifier that orchestrates the entire classification process."""

    def __init__(
        self,
        data_dir: str = "data",
        model_name: str = "gemini-2.5-flash",
        api_key: Optional[str] = None
    ):
        """Initialize the HS classifier.

        Args:
            data_dir: Directory containing HS data files
            model_name: Gemini model to use
            api_key: Google API key (if not set in environment)
        """
        # Set API key if provided (for Vertex AI, this is optional as we use ADC)
        if api_key:
            os.environ["GOOGLE_API_KEY"] = api_key

        # Initialize data loader
        self.data_loader = HSDataLoader(data_dir)
        print("Loading HS codes data...")
        self.data_loader.load_all_data()
        print(f"Loaded {len(self.data_loader.codes_2digit)} 2-digit codes, "
              f"{len(self.data_loader.codes_4digit)} 4-digit codes, "
              f"{len(self.data_loader.codes_6digit)} 6-digit codes")

        # Initialize classification agent
        self.agent = HSClassificationAgent(self.data_loader, model_name)

        # Initialize Langfuse client
        self.langfuse = get_client()

    async def classify(
        self,
        product_description: str,
        top_k: int = 10,
        verbose: bool = False
    ) -> Dict[str, Any]:
        """Classify a product description to get HS code.

        Args:
            product_description: Description of the product to classify
            top_k: Number of candidates to consider at each level
            verbose: Whether to print detailed progress

        Returns:
            Dictionary containing classification results at all levels
        """
        if verbose:
            print(f"\nClassifying: {product_description}")
            print("=" * 50)

        try:
            # Create proper hierarchical trace with nested spans
            with self.langfuse.start_as_current_span(
                name="🏗️ Complete HS Hierarchical Classification",
                input={
                    "product_description": product_description,
                    "classification_flow": "CHAPTER (2-digit) → HEADING (4-digit) → SUBHEADING (6-digit)",
                    "top_k": top_k
                }
            ) as main_span:
                # Set trace attributes
                main_span.update_trace(
                    tags=["hs-classification", "hierarchical"],
                    metadata={
                        "process": "hierarchical_classification",
                        "levels": ["2-digit", "4-digit", "6-digit"],
                        "model": str(self.agent.model)
                    }
                )

                # Perform hierarchical classification within the main trace
                results = await self.agent.classify_hierarchical(
                    product_description=product_description,
                    top_k=top_k
                )

                # Update the main trace with final results
                main_span.update_trace(
                    output={
                        "final_hs_code": results["final_code"],
                        "overall_confidence": results["overall_confidence"],
                        "chapter": results["chapter"].selected_code,
                        "heading": results["heading"].selected_code,
                        "subheading": results["subheading"].selected_code,
                        "classification_path": f"{results['chapter'].selected_code} → {results['heading'].selected_code} → {results['subheading'].selected_code}"
                    },
                    metadata={
                        "classification_levels": 3,
                        "top_k": top_k,
                        "confidence_breakdown": {
                            "chapter": results["chapter"].confidence,
                            "heading": results["heading"].confidence,
                            "subheading": results["subheading"].confidence
                        }
                    }
                )

                if verbose:
                    self._print_results(results)

                return results

        except Exception as e:
            print(f"Error during classification: {e}")
            raise

    def _print_results(self, results: Dict[str, Any]) -> None:
        """Print classification results in a formatted way."""

        print(f"\n📊 CHAPTER (2-digit): {results['chapter'].selected_code}")
        print(f"   Description: {self.data_loader.codes_2digit[results['chapter'].selected_code].description}")
        print(f"   Confidence: {results['chapter'].confidence:.2f}")
        print(f"   Reasoning: {results['chapter'].reasoning}")

        print(f"\n📋 HEADING (4-digit): {results['heading'].selected_code}")
        print(f"   Description: {self.data_loader.codes_4digit[results['heading'].selected_code].description}")
        print(f"   Confidence: {results['heading'].confidence:.2f}")
        print(f"   Reasoning: {results['heading'].reasoning}")

        print(f"\n🎯 SUBHEADING (6-digit): {results['subheading'].selected_code}")
        print(f"   Description: {self.data_loader.codes_6digit[results['subheading'].selected_code].description}")
        print(f"   Confidence: {results['subheading'].confidence:.2f}")
        print(f"   Reasoning: {results['subheading'].reasoning}")

        print(f"\n✅ FINAL HS CODE: {results['final_code']}")
        print(f"🎯 OVERALL CONFIDENCE: {results['overall_confidence']:.2f}")

    def classify_sync(
        self,
        product_description: str,
        top_k: int = 10,
        verbose: bool = False
    ) -> Dict[str, Any]:
        """Synchronous wrapper for classify method."""
        try:
            result = asyncio.run(self.classify(product_description, top_k, verbose))
            # Flush Langfuse events for short-lived applications
            self.langfuse.flush()
            return result
        except Exception as e:
            # Flush Langfuse events even on error
            self.langfuse.flush()
            raise


def create_classifier(
    data_dir: str = "data",
    model_name: str = "gemini-2.5-flash",
    api_key: Optional[str] = None
) -> HSClassifier:
    """Factory function to create an HS classifier."""
    return HSClassifier(data_dir, model_name, api_key)