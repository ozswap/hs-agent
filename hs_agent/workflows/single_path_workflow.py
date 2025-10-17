"""Single-path hierarchical classification workflow.

This workflow performs step-by-step hierarchical classification:
1. Select best chapter (2-digit)
2. Select best heading within chapter (4-digit)
3. Select best subheading within heading (6-digit)
4. Calculate final confidence score
"""

from typing import Dict, Optional

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph

from hs_agent.config_loader import get_prompt
from hs_agent.data_loader import HSDataLoader
from hs_agent.factories import ModelFactory
from hs_agent.graph_models import ClassificationState
from hs_agent.models import (
    ClassificationLevel,
    ClassificationResult,
    create_no_hs_code_result,
    is_no_hs_code,
)
from hs_agent.policies import RetryPolicy
from hs_agent.utils.logger import get_logger
from hs_agent.workflows.base_workflow import BaseWorkflow

logger = get_logger("hs_agent.workflows.single_path")


class SinglePathWorkflow(BaseWorkflow):
    """Workflow for single-path hierarchical HS code classification."""

    def __init__(
        self,
        data_loader: HSDataLoader,
        model_name: str,
        configs: Dict,
        retry_policy: RetryPolicy
    ):
        """Initialize the single-path workflow.

        Args:
            data_loader: Data loader with HS codes
            model_name: Name of the LLM model to use
            configs: Workflow configuration dictionary
            retry_policy: Retry policy for LLM invocations
        """
        self.data_loader = data_loader
        self.model_name = model_name
        self.configs = configs
        self.retry_policy = retry_policy

    def build_graph(self):
        """Build the LangGraph for hierarchical classification."""
        workflow = StateGraph(ClassificationState)

        # Add nodes for each step
        workflow.add_node("select_chapter", self._select_chapter)
        workflow.add_node("select_heading", self._select_heading)
        workflow.add_node("select_subheading", self._select_subheading)
        workflow.add_node("finalize", self._finalize)

        # Define edges
        workflow.add_edge(START, "select_chapter")
        workflow.add_edge("select_chapter", "select_heading")
        workflow.add_edge("select_heading", "select_subheading")
        workflow.add_edge("select_subheading", "finalize")
        workflow.add_edge("finalize", END)

        return workflow.compile()

    # ========== Graph Node Methods ==========

    async def _select_chapter(self, state: ClassificationState) -> ClassificationState:
        """Evaluate all chapters and select the best one."""
        result = await self._select_code(
            state["product_description"],
            self.data_loader.codes_2digit,
            ClassificationLevel.CHAPTER,
            config_name="select_chapter_candidates"
        )
        return {**state, "chapter_result": result}

    async def _select_heading(self, state: ClassificationState) -> ClassificationState:
        """Evaluate all headings under selected chapter and select the best one."""
        chapter_code = state["chapter_result"].selected_code
        codes = {c: h for c, h in self.data_loader.codes_4digit.items() if c.startswith(chapter_code)}
        result = await self._select_code(
            state["product_description"],
            codes,
            ClassificationLevel.HEADING,
            config_name="select_heading_candidates",
            parent_code=chapter_code
        )
        return {**state, "heading_result": result}

    async def _select_subheading(self, state: ClassificationState) -> ClassificationState:
        """Evaluate all subheadings under selected heading and select the best one."""
        heading_code = state["heading_result"].selected_code
        codes = {c: h for c, h in self.data_loader.codes_6digit.items() if c.startswith(heading_code)}
        result = await self._select_code(
            state["product_description"],
            codes,
            ClassificationLevel.SUBHEADING,
            config_name="select_subheading_candidates",
            parent_code=heading_code
        )
        return {**state, "subheading_result": result}

    async def _finalize(self, state: ClassificationState) -> ClassificationState:
        """Calculate final confidence and code."""
        overall_confidence = (
            state["chapter_result"].confidence * 0.3 +
            state["heading_result"].confidence * 0.3 +
            state["subheading_result"].confidence * 0.4
        )
        return {
            **state,
            "final_code": state["subheading_result"].selected_code,
            "overall_confidence": overall_confidence
        }

    # ========== Helper Methods ==========

    async def _select_code(
        self,
        product_description: str,
        codes_dict: Dict,
        level: ClassificationLevel,
        config_name: str = "select_chapter_candidates",
        parent_code: Optional[str] = None
    ) -> ClassificationResult:
        """Evaluate all codes and select the best one using config prompts."""

        # Use base class helper to format candidates
        candidates_list = self._format_candidates_list(codes_dict)

        # Use prompts from config if available
        config = self.configs.get(config_name, {})

        system_prompt = get_prompt(config, "system") or """You are an HS code classification expert.
Evaluate all codes and select the BEST one. Provide confidence (0.0-1.0) and reasoning."""

        # Build template variables
        template_vars = {
            "product_description": product_description,
            "candidates_list": candidates_list,
            "level": self._get_level_name(level)
        }

        # Use base class helper to add parent context
        self._add_parent_context(template_vars, level, parent_code)

        user_prompt = get_prompt(config, "user", **template_vars) or f"""Product: "{product_description}"

Candidates:
{candidates_list}

Evaluate all codes and select the most accurate one."""

        try:
            # Get config-specific model for this selection step
            selection_model = ModelFactory.create_with_config(self.model_name, config)

            # Invoke with retry logic
            result = await self.retry_policy.invoke_with_retry(
                selection_model,
                [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
            )

            # Handle exhausted retries - return "000000" (insufficient information)
            if result is None:
                return create_no_hs_code_result(
                    level=level,
                    confidence=0.0,
                    reasoning="Unable to classify - LLM failed to return valid response after retries"
                )

            # Handle special "000000" code for invalid descriptions
            if is_no_hs_code(result["selected_code"]):
                return create_no_hs_code_result(
                    level=level,
                    confidence=result["confidence"],
                    reasoning=result["reasoning"]
                )

            # Validate that selected code is in codes_dict
            if result["selected_code"] not in codes_dict:
                # LLM returned invalid code - this should not happen with proper schemas
                raise ValueError(f"LLM selected invalid code '{result['selected_code']}' not in codes: {list(codes_dict.keys())}")

            return ClassificationResult(
                level=level,
                selected_code=result["selected_code"],
                description=codes_dict[result["selected_code"]].description,
                confidence=result["confidence"],
                reasoning=result["reasoning"]
            )

        except Exception as e:
            logger.error(f"❌ Selection failed for config '{config_name}': {e}")
            raise RuntimeError(f"Selection failed for config '{config_name}': {e}") from e
