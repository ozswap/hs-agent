"""HS classification agent with LangGraph."""

from typing import Dict, Any, List, Optional
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_google_vertexai import ChatVertexAI
from langgraph.graph import StateGraph, START, END

from hs_agent.models import (
    ClassificationLevel,
    ClassificationResult,
    ClassificationResponse,
    MultiChoiceClassificationResponse,
    ClassificationPath
)
from hs_agent.graph_models import ClassificationState, MultiChoiceState
from hs_agent.config.settings import settings
from hs_agent.data_loader import HSDataLoader
from hs_agent.config_loader import load_workflow_configs, get_prompt, get_model_params
from hs_agent.utils.logger import get_logger

# Get centralized logger
logger = get_logger("hs_agent.agent")


class HSAgent:
    """HS classification agent using LangGraph with Langfuse tracking."""

    # Class-level constants to follow DRY principle
    LEVEL_NAMES = {"2": "CHAPTER", "4": "HEADING", "6": "SUBHEADING"}

    def __init__(
        self,
        data_loader: HSDataLoader,
        model_name: Optional[str] = None,
        workflow_name: str = "wide_net_classification"
    ):
        self.data_loader = data_loader
        self.model_name = model_name or settings.default_model_name
        self.workflow_name = workflow_name

        # Load workflow configs from files
        logger.step_start("Loading workflow configs", f"'{workflow_name}'")
        from pathlib import Path
        workflow_path = Path(f"configs/{workflow_name}")
        self.configs = load_workflow_configs(workflow_path)

        # Initialize Langfuse if enabled (SDK v3)
        self.langfuse_handler = None
        if settings.langfuse_enabled:
            try:
                from langfuse import Langfuse
                from langfuse.langchain import CallbackHandler

                # Initialize Langfuse client (SDK v3 pattern)
                Langfuse(
                    public_key=settings.langfuse_public_key,
                    secret_key=settings.langfuse_secret_key,
                    host=settings.langfuse_host
                )

                # Create callback handler (no constructor args in v3)
                self.langfuse_handler = CallbackHandler()
                logger.init_complete("Langfuse tracking", "SDK v3")
            except Exception as e:
                logger.warning(f"⚠️  Langfuse initialization failed: {e}")

        # Build LangGraphs
        self.graph = self._build_graph()
        self.multi_graph = self._build_multi_graph()

    # === DRY UTILITY METHODS ===
    
    def _get_level_name(self, level: ClassificationLevel) -> str:
        """Get human-readable level name. Follows DRY principle."""
        return self.LEVEL_NAMES[level.value]

    def _get_model_for_config(self, config_name: str, output_schema: Optional[type] = None) -> Any:
        """Create a ChatVertexAI model configured for a specific workflow step.

        Args:
            config_name: Name of the config to use (e.g., 'rank_chapter_candidates')
            output_schema: Optional Pydantic model for structured output (fallback if no dynamic model)

        Returns:
            ChatVertexAI model, optionally with structured output
        """
        # Get config-specific parameters
        config = self.configs.get(config_name, {})
        model_params = get_model_params(config)

        # Build model kwargs with config-specific parameters or defaults
        model_kwargs = {
            "model": model_params.get("model_name", self.model_name),
            "temperature": model_params.get("temperature", 0.1),
            "max_tokens": model_params.get("max_tokens", 8192),
            "top_p": model_params.get("top_p", 0.95),
        }

        # Add thinking_budget and include_thoughts if thinking is enabled (only supported in Gemini 2.5+ models)
        # Note: include_thoughts can only be used when thinking_budget is set to a positive value
        thinking_budget = model_params.get("thinking_budget")
        if thinking_budget is not None and thinking_budget > 0:
            model_kwargs["thinking_budget"] = thinking_budget
            model_kwargs["include_thoughts"] = True

        # Create base model
        model = ChatVertexAI(**model_kwargs)

        # Use JSON Schema directly from config
        if json_schema := config.get("output_schema"):
            model = model.with_structured_output(json_schema)

        return model

    def _build_graph(self):
        """Build the LangGraph for hierarchical classification."""
        workflow = StateGraph(ClassificationState)

        # Add nodes for each step (ranking and selection merged)
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

    async def classify(self, product_description: str) -> ClassificationResponse:
        """Classify a product using LangGraph with Langfuse tracking."""
        import time
        start = time.time()

        # Initial state
        initial_state: ClassificationState = {
            "product_description": product_description,
            "chapter_result": None,
            "heading_result": None,
            "subheading_result": None,
            "final_code": None,
            "overall_confidence": None
        }

        # Prepare config with Langfuse callbacks (SDK v3 pattern)
        config = {}
        if self.langfuse_handler:
            config["callbacks"] = [self.langfuse_handler]

        # Run graph with callbacks
        final_state = await self.graph.ainvoke(initial_state, config=config)

        processing_time = (time.time() - start) * 1000

        return ClassificationResponse(
            product_description=product_description,
            final_code=final_state["final_code"],
            overall_confidence=final_state["overall_confidence"],
            chapter=final_state["chapter_result"],
            heading=final_state["heading_result"],
            subheading=final_state["subheading_result"],
            processing_time_ms=processing_time
        )

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
        
        # Prepare candidates list from codes dict
        candidates_list = "\n".join([
            f"{code}: {hs.description}"
            for code, hs in codes_dict.items()
        ])
        
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
        
        # Add parent context based on level
        if parent_code:
            if level == ClassificationLevel.HEADING:
                template_vars["parent_chapter"] = parent_code
            elif level == ClassificationLevel.SUBHEADING:
                template_vars["parent_heading"] = parent_code

        user_prompt = get_prompt(config, "user", **template_vars) or f"""Product: "{product_description}"

Candidates:
{candidates_list}

Evaluate all codes and select the most accurate one."""

        try:
            # Get config-specific model for this selection step
            selection_model = self._get_model_for_config(config_name)

            result = await selection_model.ainvoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ])

            if result is None:
                raise ValueError("LLM returned None")

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

    # ========== Multi-Choice Classification ==========

    def _build_multi_graph(self):
        """Build the LangGraph for multi-choice classification (1-N paths)."""
        workflow = StateGraph(MultiChoiceState)

        # Add nodes for multi-choice workflow (ranking and selection merged)
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

    async def classify_multi(self, product_description: str, max_selections: int = 3) -> MultiChoiceClassificationResponse:
        """Classify a product and return 1-N HS code paths."""
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
            "comparison_summary": None
        }

        # Prepare config with Langfuse callbacks
        config = {}
        if self.langfuse_handler:
            config["callbacks"] = [self.langfuse_handler]

        # Run multi-choice graph
        final_state = await self.multi_graph.ainvoke(initial_state, config=config)

        processing_time = (time.time() - start) * 1000

        return MultiChoiceClassificationResponse(
            product_description=product_description,
            paths=final_state["paths"],
            overall_strategy=final_state["overall_strategy"],
            processing_time_ms=processing_time,
            final_selected_code=final_state["final_selected_code"],
            final_confidence=final_state["final_confidence"],
            final_reasoning=final_state["final_reasoning"],
            comparison_summary=final_state["comparison_summary"]
        )

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

    def _load_chapter_notes(self, chapter_codes: List[str]) -> str:
        """Load chapter notes for given chapter codes.

        Args:
            chapter_codes: List of 2-digit chapter codes (e.g., ['85', '92'])

        Returns:
            Formatted string with chapter notes
        """
        from pathlib import Path

        notes_dir = Path("data/chapters_markdown")
        if not notes_dir.exists():
            return "Chapter notes not available."

        chapter_notes = []
        for chapter_code in sorted(set(chapter_codes)):  # Remove duplicates and sort
            # Format: chapter_01_notes.md, chapter_85_notes.md, etc.
            notes_file = notes_dir / f"chapter_{chapter_code}_notes.md"

            if notes_file.exists():
                try:
                    with open(notes_file, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                        chapter_notes.append(f"═══ CHAPTER {chapter_code} NOTES ═══\n{content}")
                except Exception as e:
                    logger.warning(f"⚠️  Failed to load notes for chapter {chapter_code}: {e}")
            else:
                logger.debug(f"Notes file not found for chapter {chapter_code}")

        if not chapter_notes:
            return "No chapter notes available for the chapters in these paths."

        return "\n\n".join(chapter_notes)

    async def _compare_final_codes(self, state: MultiChoiceState) -> MultiChoiceState:
        """Compare all paths and select the single best HS code."""
        paths = state["paths"]
        product_description = state["product_description"]

        # Extract unique chapter codes from all paths
        chapter_codes = list(set(path.chapter_code for path in paths))

        # Load chapter notes for all chapters present in paths
        chapter_notes = self._load_chapter_notes(chapter_codes)

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
            comparison_model = self._get_model_for_config("compare_final_codes")

            result = await comparison_model.ainvoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ])

            if result is None:
                raise ValueError("LLM returned None")

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
            # Get config-specific model for this multi-selection step
            config = self.configs.get(config_name, {})
            
            # Get base model
            model_params = get_model_params(config)
            model_kwargs = {
                "model": model_params.get("model_name", self.model_name),
                "temperature": model_params.get("temperature", 0.1),
                "max_tokens": model_params.get("max_tokens", 8192),
                "top_p": model_params.get("top_p", 0.95),
            }
            thinking_budget = model_params.get("thinking_budget")
            if thinking_budget is not None and thinking_budget > 0:
                model_kwargs["thinking_budget"] = thinking_budget
                model_kwargs["include_thoughts"] = True
                
            base_model = ChatVertexAI(**model_kwargs)
            
            # Add enum constraints for selection schemas
            if (json_schema := config.get("output_schema")) and "select" in config_name:
                # Add enum constraint inline
                schema = json_schema.copy()
                candidate_codes = list(codes_dict.keys())
                if "properties" in schema and "selected_codes" in schema["properties"]:
                    if "items" not in schema["properties"]["selected_codes"]:
                        schema["properties"]["selected_codes"]["items"] = {}
                    schema["properties"]["selected_codes"]["items"]["enum"] = candidate_codes
                multi_selection_model = base_model.with_structured_output(schema)
            elif json_schema:
                multi_selection_model = base_model.with_structured_output(json_schema)
            else:
                multi_selection_model = base_model

            result = await multi_selection_model.ainvoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ])

            if result is None:
                raise ValueError("LLM returned None")

            # Validate that all selected codes are in codes_dict
            valid_codes = []
            valid_confidences = []

            for i, code in enumerate(result["selected_codes"]):
                if code in codes_dict:
                    valid_codes.append(code)
                    valid_confidences.append(result["individual_confidences"][i])
                else:
                    logger.warning(f"⚠️  LLM selected invalid code '{code}' not in codes, skipping")

            # If no valid codes, raise error instead of fallback
            if not valid_codes:
                raise ValueError(f"No valid codes selected. LLM selected: {result['selected_codes']}, Available: {list(codes_dict.keys())}")
            
            reasoning = result["reasoning"]

            return {
                "codes": valid_codes,
                "confidences": valid_confidences,
                "reasonings": [reasoning] * len(valid_codes)
            }

        except Exception as e:
            logger.error(f"❌ Multi-selection failed for config '{config_name}': {e}")
            raise RuntimeError(f"Multi-selection failed for config '{config_name}': {e}") from e