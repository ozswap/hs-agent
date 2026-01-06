"""HS classification agent with LangGraph."""

from hs_agent.config.settings import settings
from hs_agent.config_loader import load_workflow_configs
from hs_agent.data import ChapterNotesService, HSDataLoader
from hs_agent.graph_models import ClassificationState, MultiChoiceState
from hs_agent.models import (
    ClassificationResponse,
    MultiChoiceClassificationResponse,
)
from hs_agent.utils.logger import get_logger
from hs_agent.utils.retry import RetryPolicy
from hs_agent.workflows import MultiPathWorkflow, SinglePathWorkflow

# Get centralized logger
logger = get_logger("hs_agent.agent")


class HSAgent:
    """HS classification agent using LangGraph with Logfire tracing.

    This is a facade class that delegates to workflow classes for the actual
    classification logic. It manages:
    - Configuration loading
    - Service initialization (retry policy, chapter notes)
    - Logfire observability integration
    - Public API (classify, classify_multi methods)
    """

    def __init__(
        self,
        data_loader: HSDataLoader,
        model_name: str | None = None,
        workflow_name: str = "wide_net_classification",
    ):
        """Initialize the HS classification agent.

        Args:
            data_loader: Data loader with HS codes
            model_name: Name of the LLM model to use (defaults to settings.default_model_name)
            workflow_name: Name of the workflow configuration to use
        """
        self.data_loader = data_loader
        self.model_name = model_name or settings.default_model_name
        self.workflow_name = workflow_name

        # Load workflow configs from files
        logger.step_start("Loading workflow configs", f"'{workflow_name}'")
        from pathlib import Path

        workflow_path = Path(f"configs/{workflow_name}")
        self.configs = load_workflow_configs(workflow_path)

        # Initialize retry policy for LLM invocations
        self.retry_policy = RetryPolicy(max_retries=3, initial_delay=1.0, prompt_variation=True)

        # Initialize chapter notes service
        self.chapter_notes_service = ChapterNotesService()

        # Initialize workflows
        self.single_path_workflow = SinglePathWorkflow(
            data_loader=self.data_loader,
            model_name=self.model_name,
            configs=self.configs,
            retry_policy=self.retry_policy,
        )

        self.multi_path_workflow = MultiPathWorkflow(
            data_loader=self.data_loader,
            model_name=self.model_name,
            configs=self.configs,
            retry_policy=self.retry_policy,
            chapter_notes_service=self.chapter_notes_service,
        )

        # Build LangGraphs using workflows
        self.graph = self.single_path_workflow.build_graph()
        self.multi_graph = self.multi_path_workflow.build_graph()

    async def classify(self, product_description: str) -> ClassificationResponse:
        """Classify a product using single-path hierarchical classification.

        This method performs step-by-step hierarchical classification:
        1. Select best chapter (2-digit)
        2. Select best heading within chapter (4-digit)
        3. Select best subheading within heading (6-digit)
        4. Calculate final confidence score

        Args:
            product_description: Product description to classify

        Returns:
            ClassificationResponse with final code and confidence scores
        """
        import time

        start = time.time()

        # Initial state
        initial_state: ClassificationState = {
            "product_description": product_description,
            "chapter_result": None,
            "heading_result": None,
            "subheading_result": None,
            "final_code": None,
            "overall_confidence": None,
        }

        # Run graph (LangSmith OTEL auto-instruments via Logfire)
        final_state = await self.graph.ainvoke(initial_state)

        processing_time = (time.time() - start) * 1000

        return ClassificationResponse(
            product_description=product_description,
            final_code=final_state["final_code"],
            overall_confidence=final_state["overall_confidence"],
            chapter=final_state["chapter_result"],
            heading=final_state["heading_result"],
            subheading=final_state["subheading_result"],
            processing_time_ms=processing_time,
        )

    async def classify_multi(
        self, product_description: str, max_selections: int = 3
    ) -> MultiChoiceClassificationResponse:
        """Classify a product using multi-path classification with comparison.

        This method explores multiple classification paths simultaneously:
        1. Select top N chapters (2-digit)
        2. For each chapter, select top N headings (4-digit)
        3. For each heading, select top N subheadings (6-digit)
        4. Build all possible classification paths
        5. Compare paths using chapter notes and select the single best HS code

        Args:
            product_description: Product description to classify
            max_selections: Maximum number of codes to select at each level (default: 3)

        Returns:
            MultiChoiceClassificationResponse with all paths and final selected code
        """
        import time

        start = time.time()

        # Initial state
        initial_state: MultiChoiceState = {
            "product_description": product_description,
            "max_selections": max_selections,
            "selected_chapters": None,
            "chapter_confidences": None,
            "chapter_reasonings": None,
            "selected_headings_by_chapter": None,
            "heading_confidences_by_chapter": None,
            "heading_reasonings_by_chapter": None,
            "selected_subheadings_by_heading": None,
            "subheading_confidences_by_heading": None,
            "subheading_reasonings_by_heading": None,
            "paths": None,
            "overall_strategy": None,
            "final_selected_code": None,
            "final_confidence": None,
            "final_reasoning": None,
            "comparison_summary": None,
        }

        # Run multi-choice graph (LangSmith OTEL auto-instruments via Logfire)
        final_state = await self.multi_graph.ainvoke(initial_state)

        processing_time = (time.time() - start) * 1000

        return MultiChoiceClassificationResponse(
            product_description=product_description,
            paths=final_state["paths"],
            overall_strategy=final_state["overall_strategy"],
            processing_time_ms=processing_time,
            final_selected_code=final_state["final_selected_code"],
            final_confidence=final_state["final_confidence"],
            final_reasoning=final_state["final_reasoning"],
            comparison_summary=final_state["comparison_summary"],
        )
