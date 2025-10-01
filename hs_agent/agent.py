"""HS classification agent with LangGraph."""

from typing import Dict, Any, List, Optional
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_google_vertexai import ChatVertexAI
from langgraph.graph import StateGraph, START, END

from hs_agent.models import (
    ClassificationLevel,
    RankingOutput,
    SelectionOutput,
    ClassificationResult,
    ClassificationResponse
)
from hs_agent.graph_models import ClassificationState
from hs_agent.config.settings import settings
from hs_agent.data_loader import HSDataLoader
from hs_agent.config_loader import load_workflow_configs, get_prompt, get_model_params


class HSAgent:
    """HS classification agent using LangGraph with Langfuse tracking."""

    def __init__(self, data_loader: HSDataLoader, model_name: Optional[str] = None):
        self.data_loader = data_loader
        self.model_name = model_name or settings.default_model_name

        # Load workflow configs from files
        print("Loading workflow configs...")
        self.configs = load_workflow_configs()

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
                print(f"✅ Langfuse tracking enabled (SDK v3)")
            except Exception as e:
                print(f"⚠️  Langfuse initialization failed: {e}")

        # Initialize models
        self.model = ChatVertexAI(model=self.model_name)
        self.ranking_model = self.model.with_structured_output(RankingOutput)
        self.selection_model = self.model.with_structured_output(SelectionOutput)

        # Build LangGraph
        self.graph = self._build_graph()

    def _build_graph(self):
        """Build the LangGraph for hierarchical classification."""
        workflow = StateGraph(ClassificationState)

        # Add nodes for each step
        workflow.add_node("rank_chapters", self._rank_chapters)
        workflow.add_node("select_chapter", self._select_chapter)
        workflow.add_node("rank_headings", self._rank_headings)
        workflow.add_node("select_heading", self._select_heading)
        workflow.add_node("rank_subheadings", self._rank_subheadings)
        workflow.add_node("select_subheading", self._select_subheading)
        workflow.add_node("finalize", self._finalize)

        # Define edges
        workflow.add_edge(START, "rank_chapters")
        workflow.add_edge("rank_chapters", "select_chapter")
        workflow.add_edge("select_chapter", "rank_headings")
        workflow.add_edge("rank_headings", "select_heading")
        workflow.add_edge("select_heading", "rank_subheadings")
        workflow.add_edge("rank_subheadings", "select_subheading")
        workflow.add_edge("select_subheading", "finalize")
        workflow.add_edge("finalize", END)

        return workflow.compile()

    async def classify(self, product_description: str, top_k: int = 10) -> ClassificationResponse:
        """Classify a product using LangGraph with Langfuse tracking."""
        import time
        start = time.time()

        # Initial state
        initial_state: ClassificationState = {
            "product_description": product_description,
            "top_k": top_k,
            "chapter_candidates": None,
            "chapter_result": None,
            "heading_candidates": None,
            "heading_result": None,
            "subheading_candidates": None,
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

    async def _rank_chapters(self, state: ClassificationState) -> ClassificationState:
        """Rank chapter candidates."""
        ranked = await self._rank_codes(
            state["product_description"],
            self.data_loader.codes_2digit,
            state["top_k"]
        )
        return {**state, "chapter_candidates": ranked}

    async def _select_chapter(self, state: ClassificationState) -> ClassificationState:
        """Select best chapter."""
        result = await self._select_code(
            state["product_description"],
            state["chapter_candidates"],
            ClassificationLevel.CHAPTER
        )
        return {**state, "chapter_result": result}

    async def _rank_headings(self, state: ClassificationState) -> ClassificationState:
        """Rank heading candidates under selected chapter."""
        chapter_code = state["chapter_result"].selected_code
        codes = {c: h for c, h in self.data_loader.codes_4digit.items() if c.startswith(chapter_code)}
        ranked = await self._rank_codes(state["product_description"], codes, state["top_k"])
        return {**state, "heading_candidates": ranked}

    async def _select_heading(self, state: ClassificationState) -> ClassificationState:
        """Select best heading."""
        result = await self._select_code(
            state["product_description"],
            state["heading_candidates"],
            ClassificationLevel.HEADING
        )
        return {**state, "heading_result": result}

    async def _rank_subheadings(self, state: ClassificationState) -> ClassificationState:
        """Rank subheading candidates under selected heading."""
        heading_code = state["heading_result"].selected_code
        codes = {c: h for c, h in self.data_loader.codes_6digit.items() if c.startswith(heading_code)}
        ranked = await self._rank_codes(state["product_description"], codes, state["top_k"])
        return {**state, "subheading_candidates": ranked}

    async def _select_subheading(self, state: ClassificationState) -> ClassificationState:
        """Select best subheading."""
        result = await self._select_code(
            state["product_description"],
            state["subheading_candidates"],
            ClassificationLevel.SUBHEADING
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

    async def _rank_codes(self, product_description: str, codes_dict: Dict, top_k: int) -> List[Dict]:
        """Rank HS codes by relevance using config prompts."""
        # Prepare candidates list
        candidates_list = "\n".join([
            f"{i+1}. {code}: {hs.description}"
            for i, (code, hs) in enumerate(codes_dict.items())
        ])

        # Use prompts from config if available
        config = self.configs.get("rank_chapter_candidates", {})

        system_prompt = get_prompt(config, "system") or """You are an HS code classification expert.
Rank candidates by relevance (0.0-1.0 score)."""

        user_prompt = get_prompt(
            config, "user",
            product_description=product_description,
            candidates_list=candidates_list
        ) or f"""Product: "{product_description}"

Codes:
{candidates_list}

Rank top {top_k} most relevant codes."""

        try:
            result = await self.ranking_model.ainvoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ])

            # Convert to dict format
            return [
                {"code": c.code, "description": c.description, "relevance_score": c.relevance_score}
                for c in result.ranked_candidates if c.code in codes_dict
            ][:top_k]

        except Exception as e:
            print(f"Ranking failed: {e}, using fallback")
            return [
                {"code": code, "description": hs.description, "relevance_score": max(0.1, 0.8 - i * 0.1)}
                for i, (code, hs) in enumerate(list(codes_dict.items())[:top_k])
            ]

    async def _select_code(self, product_description: str, candidates: List[Dict], level: ClassificationLevel) -> ClassificationResult:
        """Select best code from candidates using config prompts."""
        level_names = {"2": "CHAPTER", "4": "HEADING", "6": "SUBHEADING"}

        # Prepare candidate summaries
        ranked_candidates_summary = ", ".join([c['code'] for c in candidates[:5]])
        ranked_candidates_detailed = "\n".join([
            f"{i+1}. Code: {c['code']} | Score: {c['relevance_score']:.2f} | {c['description']}"
            for i, c in enumerate(candidates)
        ])

        # Use prompts from config if available
        config = self.configs.get("select_chapter_candidates", {})

        system_prompt = get_prompt(config, "system") or """You are an HS code classification expert.
Select the BEST code. Provide confidence (0.0-1.0) and reasoning."""

        user_prompt = get_prompt(
            config, "user",
            product_description=product_description,
            ranked_candidates_summary=ranked_candidates_summary,
            ranked_candidates_detailed=ranked_candidates_detailed,
            level=level_names[level.value]
        ) or f"""Product: "{product_description}"
Level: {level_names[level.value]}

Candidates:
{ranked_candidates_detailed}

Select the most accurate code."""

        try:
            result = await self.selection_model.ainvoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ])

            if result is None:
                raise ValueError("LLM returned None")

            return ClassificationResult(
                level=level,
                selected_code=result.selected_code,
                confidence=result.confidence,
                reasoning=result.reasoning
            )

        except Exception as e:
            print(f"Selection failed: {e}, using fallback")
            if candidates:
                return ClassificationResult(
                    level=level,
                    selected_code=candidates[0]["code"],
                    confidence=0.5,
                    reasoning=f"Fallback: {e}"
                )
            else:
                return ClassificationResult(
                    level=level,
                    selected_code="000000",
                    confidence=0.0,
                    reasoning=f"No candidates: {e}"
                )