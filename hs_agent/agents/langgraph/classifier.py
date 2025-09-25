"""Main LangGraph HS classifier orchestrator."""

# Standard library imports
import asyncio
from typing import Optional, Dict, Any

# Third-party imports
from langfuse import get_client

# Local imports
from hs_agent.config import settings
from hs_agent.core.data_loader import HSDataLoader
from hs_agent.core.logging import get_logger
from hs_agent.agents.langgraph.agents import HSLangGraphAgent
from hs_agent.agents.langgraph.models import FinalClassification, ClassificationResult

logger = get_logger(__name__)


class HSLangGraphClassifier:
    """Main LangGraph HS code classifier that orchestrates the entire classification process."""

    def __init__(
        self,
        model_name: Optional[str] = None
    ):
        """Initialize the LangGraph HS classifier.

        Args:
            model_name: Gemini model to use (defaults to settings.default_model_name)
        """
        # Initialize data loader using settings
        self.data_loader = HSDataLoader()
        logger.info("Loading HS codes data...")
        self.data_loader.load_all_data()
        logger.info(f"Loaded {len(self.data_loader.codes_2digit)} 2-digit codes, "
                    f"{len(self.data_loader.codes_4digit)} 4-digit codes, "
                    f"{len(self.data_loader.codes_6digit)} 6-digit codes")

        # Initialize LangGraph classification agent
        self.agent = HSLangGraphAgent(self.data_loader, model_name)

        # Langfuse tracing is handled automatically by the callback handler in the agent

    async def classify(
        self,
        product_description: str,
        top_k: int = 10,
        verbose: bool = False
    ) -> Dict[str, Any]:
        """Classify a product description to get HS code using LangGraph.

        Args:
            product_description: Description of the product to classify
            top_k: Number of candidates to consider at each level
            verbose: Whether to print detailed progress

        Returns:
            Dictionary containing classification results at all levels
        """
        if verbose:
            print(f"\n🚀 LangGraph Classifying: {product_description}")
            print("=" * 50)

        try:
            # Perform hierarchical classification using LangGraph workflow
            results = await self.agent.classify_hierarchical(
                product_description=product_description,
                top_k=top_k
            )

            if verbose:
                self._print_results(results)

            return results

        except Exception as e:
            print(f"Error during LangGraph classification: {e}")
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
            # LangChain callback handler automatically handles tracing
            return result
        except Exception as e:
            # LangChain callback handler automatically handles tracing
            raise


def create_langgraph_classifier(
    model_name: Optional[str] = None
) -> HSLangGraphClassifier:
    """Factory function to create a LangGraph HS classifier."""
    return HSLangGraphClassifier(model_name)