"""Multi-path classification workflow with path comparison.

This workflow explores multiple classification paths simultaneously:
1. Select top N chapters (2-digit)
2. For each chapter, select top N headings (4-digit)
3. For each heading, select top N subheadings (6-digit)
4. Build all possible classification paths
5. Compare paths using chapter notes and select the single best HS code
"""

from typing import Any, Dict, List, Optional

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph

from hs_agent.config.settings import settings
from hs_agent.config_loader import get_prompt
from hs_agent.data_loader import HSDataLoader
from hs_agent.factories import ModelFactory
from hs_agent.graph_models import MultiChoiceState
from hs_agent.models import (
    NO_HS_CODE,
    ClassificationLevel,
    ClassificationPath,
    is_no_hs_code,
)
from hs_agent.policies import RetryPolicy
from hs_agent.services import ChapterNotesService
from hs_agent.utils.logger import get_logger

logger = get_logger("hs_agent.workflows.multi_path")


class MultiPathWorkflow:
    """Workflow for multi-path HS code classification with path comparison."""

    # Class-level constants
    LEVEL_NAMES = {"2": "CHAPTER", "4": "HEADING", "6": "SUBHEADING"}

    def __init__(
        self,
        data_loader: HSDataLoader,
        model_name: str,
        configs: Dict,
        retry_policy: RetryPolicy,
        chapter_notes_service: ChapterNotesService
    ):
        """Initialize the multi-path workflow.

        Args:
            data_loader: Data loader with HS codes
            model_name: Name of the LLM model to use
            configs: Workflow configuration dictionary
            retry_policy: Retry policy for LLM invocations
            chapter_notes_service: Service for loading chapter notes
        """
        self.data_loader = data_loader
        self.model_name = model_name
        self.configs = configs
        self.retry_policy = retry_policy
        self.chapter_notes_service = chapter_notes_service

    def _get_level_name(self, level: ClassificationLevel) -> str:
        """Get human-readable level name."""
        return self.LEVEL_NAMES[level.value]

    def build_graph(self):
        """Build the LangGraph for multi-choice classification (1-N paths)."""
        workflow = StateGraph(MultiChoiceState)

        # Add nodes for multi-choice workflow
        workflow.add_node("select_chapters", self._multi_select_chapters)
        workflow.add_node("select_headings", self._multi_select_headings)
        workflow.add_node("select_subheadings", self._multi_select_subheadings)
        workflow.add_node("build_paths", self._multi_build_paths)
        workflow.add_node("compare_final_codes", self._compare_final_codes)

        # Define edges
        workflow.add_edge(START, "select_chapters")
        workflow.add_edge("select_chapters", "select_headings")
        workflow.add_edge("select_headings", "select_subheadings")
        workflow.add_edge("select_subheadings", "build_paths")
        workflow.add_edge("build_paths", "compare_final_codes")
        workflow.add_edge("compare_final_codes", END)

        return workflow.compile()

    # ========== Multi-Choice Graph Nodes ==========

    async def _multi_select_chapters(self, state: MultiChoiceState) -> MultiChoiceState:
        """Evaluate all chapters and select 1-N best."""
        result = await self._multi_select_codes(
            state["product_description"],
            self.data_loader.codes_2digit,
            "select_chapter_candidates",
            ClassificationLevel.CHAPTER,
            max_selections=state["max_selections"]
        )
        return {
            **state,
            "selected_chapters": result["codes"],
            "chapter_confidences": result["confidences"],
            "chapter_reasonings": result["reasonings"]
        }

    async def _multi_select_headings(self, state: MultiChoiceState) -> MultiChoiceState:
        """Evaluate all headings for each chapter and select 1-N best."""
        selected_headings = {}
        confidences = {}
        reasonings = {}

        for chapter_code in state["selected_chapters"]:
            codes = {c: h for c, h in self.data_loader.codes_4digit.items() if c.startswith(chapter_code)}
            result = await self._multi_select_codes(
                state["product_description"],
                codes,
                "select_heading_candidates",
                ClassificationLevel.HEADING,
                max_selections=state["max_selections"],
                parent_code=chapter_code
            )
            selected_headings[chapter_code] = result["codes"]
            confidences[chapter_code] = result["confidences"]
            reasonings[chapter_code] = result["reasonings"]

        return {
            **state,
            "selected_headings_by_chapter": selected_headings,
            "heading_confidences_by_chapter": confidences,
            "heading_reasonings_by_chapter": reasonings
        }

    async def _multi_select_subheadings(self, state: MultiChoiceState) -> MultiChoiceState:
        """Evaluate all subheadings for each heading and select 1-N best."""
        selected_subheadings = {}
        confidences = {}
        reasonings = {}

        for chapter_code, headings in state["selected_headings_by_chapter"].items():
            for heading_code in headings:
                codes = {c: h for c, h in self.data_loader.codes_6digit.items() if c.startswith(heading_code)}
                result = await self._multi_select_codes(
                    state["product_description"],
                    codes,
                    "select_subheading_candidates",
                    ClassificationLevel.SUBHEADING,
                    max_selections=state["max_selections"],
                    parent_code=heading_code
                )
                selected_subheadings[heading_code] = result["codes"]
                confidences[heading_code] = result["confidences"]
                reasonings[heading_code] = result["reasonings"]

        return {
            **state,
            "selected_subheadings_by_heading": selected_subheadings,
            "subheading_confidences_by_heading": confidences,
            "subheading_reasonings_by_heading": reasonings
        }

    async def _multi_build_paths(self, state: MultiChoiceState) -> MultiChoiceState:
        """Build all complete classification paths from selections."""
        paths = []

        # Build all possible paths
        for i, chapter_code in enumerate(state["selected_chapters"]):
            chapter_reasoning = state["chapter_reasonings"][i]

            for j, heading_code in enumerate(state["selected_headings_by_chapter"][chapter_code]):
                heading_reasoning = state["heading_reasonings_by_chapter"][chapter_code][j]

                for k, subheading_code in enumerate(state["selected_subheadings_by_heading"][heading_code]):
                    subheading_reasoning = state["subheading_reasonings_by_heading"][heading_code][k]

                    # Calculate path confidence
                    chapter_conf = state["chapter_confidences"][i]
                    heading_conf = state["heading_confidences_by_chapter"][chapter_code][j]
                    subheading_conf = state["subheading_confidences_by_heading"][heading_code][k]
                    path_confidence = (chapter_conf * 0.3 + heading_conf * 0.3 + subheading_conf * 0.4)

                    # Get descriptions from data loader
                    chapter_desc = self.data_loader.codes_2digit.get(chapter_code, None)
                    heading_desc = self.data_loader.codes_4digit.get(heading_code, None)
                    subheading_desc = self.data_loader.codes_6digit.get(subheading_code, None)

                    paths.append(ClassificationPath(
                        chapter_code=chapter_code,
                        chapter_description=chapter_desc.description if chapter_desc else "Description not found",
                        heading_code=heading_code,
                        heading_description=heading_desc.description if heading_desc else "Description not found",
                        subheading_code=subheading_code,
                        subheading_description=subheading_desc.description if subheading_desc else "Description not found",
                        path_confidence=path_confidence,
                        chapter_reasoning=chapter_reasoning,
                        heading_reasoning=heading_reasoning,
                        subheading_reasoning=subheading_reasoning
                    ))

        # Sort by confidence and limit to configured max to avoid overwhelming output
        paths.sort(key=lambda p: p.path_confidence, reverse=True)
        top_paths = paths[:settings.max_output_paths]

        overall_strategy = f"Selected {len(top_paths)} classification path(s) from {len(paths)} possible combinations"

        return {**state, "paths": top_paths, "overall_strategy": overall_strategy}

    async def _compare_final_codes(self, state: MultiChoiceState) -> MultiChoiceState:
        """Compare all paths and select the single best HS code."""
        paths = state["paths"]
        product_description = state["product_description"]

        # Extract unique chapter codes from all paths
        chapter_codes = list(set(path.chapter_code for path in paths))

        # Load chapter notes for all chapters present in paths
        chapter_notes = self.chapter_notes_service.load_chapter_notes(chapter_codes)

        # Format paths for comparison
        classification_paths = "\n\n".join([
            f"PATH {i+1} (Confidence: {path.path_confidence:.2f}):\n"
            f"  Final HS Code: {path.subheading_code}\n"
            f"  Complete Path: {path.chapter_code} -> {path.heading_code} -> {path.subheading_code}\n"
            f"  Chapter: {path.chapter_code} - {path.chapter_description}\n"
            f"    Reasoning: {path.chapter_reasoning}\n"
            f"  Heading: {path.heading_code} - {path.heading_description}\n"
            f"    Reasoning: {path.heading_reasoning}\n"
            f"  Subheading: {path.subheading_code} - {path.subheading_description}\n"
            f"    Reasoning: {path.subheading_reasoning}\n"
            for i, path in enumerate(paths)
        ])

        # Use prompts from config
        config = self.configs.get("compare_final_codes", {})

        system_prompt = get_prompt(config, "system") or """You are an HS code classification expert.
Compare all classification paths and select THE SINGLE BEST HS code."""

        # Build template variables
        template_vars = {
            "product_description": product_description,
            "classification_paths": classification_paths,
            "path_count": len(paths),
            "chapter_notes": chapter_notes
        }

        user_prompt = get_prompt(config, "user", **template_vars) or f"""Product: "{product_description}"

Paths to compare:
{classification_paths}

Chapter Notes (IMPORTANT - these contain precedence rules and exclusions):
{chapter_notes}

Select the SINGLE BEST HS code from these {len(paths)} paths."""

        try:
            # Get config-specific model for comparison
            comparison_model = ModelFactory.create_with_config(self.model_name, config)

            # Invoke with retry logic
            result = await self.retry_policy.invoke_with_retry(
                comparison_model,
                [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
            )

            # Handle exhausted retries - return "000000" (insufficient information)
            if result is None:
                return {
                    **state,
                    "final_selected_code": NO_HS_CODE,
                    "final_confidence": 0.0,
                    "final_reasoning": "Unable to classify - LLM failed to return valid response after retries",
                    "comparison_summary": "Classification failed due to LLM errors"
                }

            # Handle special "000000" code for invalid descriptions
            if is_no_hs_code(result["selected_code"]):
                return {
                    **state,
                    "final_selected_code": NO_HS_CODE,
                    "final_confidence": result["confidence"],
                    "final_reasoning": result["reasoning"],
                    "comparison_summary": result["comparison_summary"]
                }

            # Validate that selected code is in one of the paths
            path_codes = {path.subheading_code for path in paths}
            if result["selected_code"] not in path_codes:
                raise ValueError(f"LLM selected invalid code '{result['selected_code']}' not in available paths: {list(path_codes)}")

            return {
                **state,
                "final_selected_code": result["selected_code"],
                "final_confidence": result["confidence"],
                "final_reasoning": result["reasoning"],
                "comparison_summary": result["comparison_summary"]
            }

        except Exception as e:
            logger.error(f"❌ Comparison failed: {e}")
            raise RuntimeError(f"Final code comparison failed: {e}") from e

    async def _multi_select_codes(
        self,
        product_description: str,
        codes_dict: Dict,
        config_name: str,
        level: ClassificationLevel,
        max_selections: int = 3,
        parent_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """Evaluate all codes and select 1-N best using multi-selection."""

        # Prepare candidates list from codes dict
        candidates_list = "\n".join([
            f"{code}: {hs.description}"
            for code, hs in codes_dict.items()
        ])

        # Get config
        config = self.configs.get(config_name, {})

        system_prompt = get_prompt(config, "system") or f"""You are an HS code classification expert.
Evaluate all codes and select 1-{max_selections} BEST codes. Provide confidence (0.0-1.0) for each and overall reasoning."""

        # Build template variables
        template_vars = {
            "product_description": product_description,
            "candidates_list": candidates_list,
            "level": self._get_level_name(level),
            "max_selections": max_selections
        }

        # Add parent context based on level
        if parent_code:
            if level == ClassificationLevel.HEADING:
                template_vars["parent_chapter"] = parent_code
            elif level == ClassificationLevel.SUBHEADING:
                template_vars["parent_heading"] = parent_code

        user_prompt = get_prompt(config, "user", **template_vars) or f"""Product: "{product_description}"
Level: {self._get_level_name(level)}
Parent: {parent_code if parent_code else 'None'}

Candidates:
{candidates_list}

Evaluate all codes and select 1-{max_selections} most accurate codes."""

        try:
            # Use ModelFactory for multi-selection with enum constraints
            multi_selection_model = ModelFactory.create_for_multi_selection(
                self.model_name,
                config,
                list(codes_dict.keys())
            )

            # Invoke with retry logic
            result = await self.retry_policy.invoke_with_retry(
                multi_selection_model,
                [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
            )

            # Handle exhausted retries - return "000000" (insufficient information)
            if result is None:
                return {
                    "codes": [NO_HS_CODE],
                    "confidences": [0.0],
                    "reasonings": ["Unable to classify - LLM failed to return valid response after retries"]
                }

            # Validate that all selected codes are in codes_dict
            valid_codes = []
            valid_confidences = []
            valid_reasonings = []

            # Handle new unified "selections" structure
            selections = result.get("selections", [])

            # Handle empty selections - return "000000" instead of raising error
            if not selections:
                logger.warning("⚠️  LLM returned empty selections array - will return 000000")
                return {
                    "codes": [NO_HS_CODE],
                    "confidences": [0.0],
                    "reasonings": ["Unable to classify - LLM returned empty selections"]
                }

            for selection in selections:
                code = selection.get("code")
                confidence = selection.get("confidence", 0.5)
                reasoning = selection.get("reasoning", "No reasoning provided")

                if not code:
                    logger.warning("⚠️  Selection missing 'code' field, skipping")
                    continue

                if code in codes_dict:
                    valid_codes.append(code)
                    valid_confidences.append(confidence)
                    valid_reasonings.append(reasoning)
                else:
                    logger.warning(f"⚠️  LLM selected invalid code '{code}' not in codes, skipping")

            # If no valid codes, return "000000" instead of raising error
            if not valid_codes:
                selected_codes = [s.get("code") for s in selections]
                logger.warning(
                    f"⚠️  No valid codes selected - will return 000000. "
                    f"LLM selected: {selected_codes}, Available: {list(codes_dict.keys())[:10]}..."
                )
                return {
                    "codes": [NO_HS_CODE],
                    "confidences": [0.0],
                    "reasonings": [f"Unable to classify - LLM selected invalid codes: {selected_codes}"]
                }

            return {
                "codes": valid_codes,
                "confidences": valid_confidences,
                "reasonings": valid_reasonings
            }

        except Exception as e:
            logger.error(f"❌ Multi-selection failed for config '{config_name}': {e}")
            raise RuntimeError(f"Multi-selection failed for config '{config_name}': {e}") from e
