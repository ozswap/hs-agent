"""LangGraph agents for HS code classification."""

# Standard library imports
from typing import List, Dict, Any, Optional
import asyncio
import concurrent.futures
from functools import partial

# Third-party imports
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_google_vertexai import ChatVertexAI
from langfuse import Langfuse, get_client
from langfuse.langchain import CallbackHandler
from langgraph.graph import StateGraph, START, END

# Local imports
from hs_agent.agents.langgraph.models import (
    HSClassificationState,
    HSMultiChoiceState,
    ClassificationLevel,
    HSCandidate,
    ClassificationResult,
    ClassificationPath,
    RankedCandidate,
    RankingOutput,
    SelectionOutput,
    MultiSelectionOutput
)
from hs_agent.config import settings
from hs_agent.core.data_loader import HSDataLoader
from hs_agent.core.exceptions import AgentError
from hs_agent.core.logging import get_logger

# Initialize logger
logger = get_logger(__name__)


class HSLangGraphAgent:
    """LangGraph-based HS classification agent with hierarchical workflow."""

    def __init__(self, data_loader: HSDataLoader, model_name: Optional[str] = None):
        self.data_loader = data_loader
        
        # Use configured model name or default
        self.model_name = model_name or settings.default_model_name
        
        try:
            # Initialize Vertex AI model
            self.model = ChatVertexAI(model=self.model_name)
            
            logger.info(
                "🤖 LangGraph agent initialized",
                model_name=self.model_name,
                langfuse_enabled=settings.langfuse_enabled
            )
            
        except Exception as e:
            error_msg = f"Failed to initialize LangGraph agent: {str(e)}"
            logger.error(error_msg, model_name=self.model_name)
            raise AgentError(
                message=error_msg,
                error_code="AGENT_INITIALIZATION_FAILED",
                details={"model_name": self.model_name, "original_error": str(e)},
                cause=e
            )

        # Initialize Langfuse callback handler if enabled
        if settings.langfuse_enabled:
            try:
                # Initialize Langfuse client with SDK v3 pattern
                Langfuse(
                    public_key=settings.langfuse_public_key,
                    secret_key=settings.langfuse_secret_key,
                    host=settings.langfuse_host
                )
                
                # Create callback handler - no constructor arguments in v3
                self.langfuse_handler = CallbackHandler()
                
                logger.info(
                    "✅ Langfuse callback handler initialized (SDK v3)",
                    host=settings.langfuse_host,
                    public_key_prefix=settings.langfuse_public_key[:10] + "..." if settings.langfuse_public_key else None
                )
            except Exception as e:
                logger.warning(f"⚠️ Langfuse handler initialization failed: {e}")
                self.langfuse_handler = None
        else:
            self.langfuse_handler = None
            logger.info("Langfuse observability disabled")

        # Initialize structured output models
        self.ranking_model = self.model.with_structured_output(RankingOutput)
        self.selection_model = self.model.with_structured_output(SelectionOutput)
        self.multi_selection_model = self.model.with_structured_output(MultiSelectionOutput)

        # Build the main hierarchical classification graph
        self.classification_graph = self._build_classification_graph()

        # Build the multi-choice looping classification graph
        self.multi_choice_graph = self._build_multi_choice_graph()

    def _build_classification_graph(self):
        """Build the main hierarchical HS classification StateGraph with one node per LLM call."""
        try:
            # Create the main workflow graph
            workflow = StateGraph(HSClassificationState)

            # Add nodes - each LLM call gets its own node with informative name
            workflow.add_node("rank_chapter_candidates", self._rank_chapter_candidates_node)
            workflow.add_node("select_best_chapter", self._select_best_chapter_node)
            workflow.add_node("rank_heading_candidates", self._rank_heading_candidates_node)
            workflow.add_node("select_best_heading", self._select_best_heading_node)
            workflow.add_node("rank_subheading_candidates", self._rank_subheading_candidates_node)
            workflow.add_node("select_best_subheading", self._select_best_subheading_node)
            workflow.add_node("finalize_classification", self._finalize_classification_node)

            # Define the sequential flow with clear LLM operation steps
            workflow.add_edge(START, "rank_chapter_candidates")
            workflow.add_edge("rank_chapter_candidates", "select_best_chapter")
            workflow.add_edge("select_best_chapter", "rank_heading_candidates")
            workflow.add_edge("rank_heading_candidates", "select_best_heading")
            workflow.add_edge("select_best_heading", "rank_subheading_candidates")
            workflow.add_edge("rank_subheading_candidates", "select_best_subheading")
            workflow.add_edge("select_best_subheading", "finalize_classification")
            workflow.add_edge("finalize_classification", END)

            # Compile the graph
            compiled_graph = workflow.compile()
            logger.info("✅ Classification graph compiled successfully")
            return compiled_graph
            
        except Exception as e:
            logger.error(f"Failed to build classification graph: {e}")
            raise

    # =============================================================================
    # LLM CALL NODES - Each node performs ONE specific LLM operation
    # =============================================================================

    async def _rank_chapter_candidates_node(self, state: HSClassificationState) -> HSClassificationState:
        """LLM Node: Rank all 97 HS chapter candidates based on product relevance."""
        codes_dict = self.data_loader.codes_2digit
        candidates = await self._llm_initial_ranking(
            state["product_description"],
            codes_dict,
            ClassificationLevel.CHAPTER,
            None,
            state["top_k"]
        )

        candidate_dicts = [
            {
                "code": code,
                "description": hs_code.description,
                "relevance_score": score
            }
            for code, hs_code, score in candidates
        ]

        return {
            **state,
            "current_level": ClassificationLevel.CHAPTER,
            "chapter_candidates": candidate_dicts
        }

    async def _select_best_chapter_node(self, state: HSClassificationState) -> HSClassificationState:
        """LLM Node: Select the best chapter from ranked candidates with detailed reasoning."""
        result = await self._llm_final_selection(
            state["product_description"],
            state["chapter_candidates"],
            ClassificationLevel.CHAPTER,
            None
        )

        return {
            **state,
            "chapter_result": result
        }

    async def _rank_heading_candidates_node(self, state: HSClassificationState) -> HSClassificationState:
        """LLM Node: Rank heading candidates under selected chapter."""
        parent_code = state["chapter_result"].selected_code
        codes_dict = {
            code: hs_code for code, hs_code in self.data_loader.codes_4digit.items()
            if code.startswith(parent_code)
        }

        candidates = await self._llm_initial_ranking(
            state["product_description"],
            codes_dict,
            ClassificationLevel.HEADING,
            parent_code,
            state["top_k"]
        )

        candidate_dicts = [
            {
                "code": code,
                "description": hs_code.description,
                "relevance_score": score
            }
            for code, hs_code, score in candidates
        ]

        return {
            **state,
            "current_level": ClassificationLevel.HEADING,
            "heading_candidates": candidate_dicts
        }

    async def _select_best_heading_node(self, state: HSClassificationState) -> HSClassificationState:
        """LLM Node: Select the best heading from ranked candidates with detailed reasoning."""
        result = await self._llm_final_selection(
            state["product_description"],
            state["heading_candidates"],
            ClassificationLevel.HEADING,
            state["chapter_result"].selected_code
        )

        return {
            **state,
            "heading_result": result
        }

    async def _rank_subheading_candidates_node(self, state: HSClassificationState) -> HSClassificationState:
        """LLM Node: Rank subheading candidates under selected heading."""
        parent_code = state["heading_result"].selected_code
        codes_dict = {
            code: hs_code for code, hs_code in self.data_loader.codes_6digit.items()
            if code.startswith(parent_code)
        }

        # Check if we have any subheading codes under this heading
        if not codes_dict:
            print(f"Warning: No subheading codes found under heading {parent_code}")
            # Create a fallback candidate using the parent heading code
            candidate_dicts = [{
                "code": parent_code + ".00",  # Default subheading
                "description": f"General subheading under {parent_code}",
                "relevance_score": 0.5
            }]
        else:
            candidates = await self._llm_initial_ranking(
                state["product_description"],
                codes_dict,
                ClassificationLevel.SUBHEADING,
                parent_code,
                state["top_k"]
            )

            candidate_dicts = [
                {
                    "code": code,
                    "description": hs_code.description,
                    "relevance_score": score
                }
                for code, hs_code, score in candidates
            ]

        return {
            **state,
            "current_level": ClassificationLevel.SUBHEADING,
            "subheading_candidates": candidate_dicts
        }

    async def _select_best_subheading_node(self, state: HSClassificationState) -> HSClassificationState:
        """LLM Node: Select the best subheading from ranked candidates with detailed reasoning."""
        result = await self._llm_final_selection(
            state["product_description"],
            state["subheading_candidates"],
            ClassificationLevel.SUBHEADING,
            state["heading_result"].selected_code
        )

        return {
            **state,
            "subheading_result": result
        }

    async def _finalize_classification_node(self, state: HSClassificationState) -> HSClassificationState:
        """Non-LLM Node: Calculate overall confidence and finalize classification results."""
        # Calculate overall confidence (weighted average)
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

    # =============================================================================
    # LLM HELPER METHODS - Used by nodes above
    # =============================================================================

    async def _llm_final_selection(
        self,
        product_description: str,
        candidate_dicts: List[Dict],
        level: ClassificationLevel,
        parent_code: str = None
    ) -> ClassificationResult:
        """Use LLM for final selection with detailed reasoning."""

        level_names = {"2": "CHAPTER", "4": "HEADING", "6": "SUBHEADING"}
        parent_context = f"🔗 Under Parent Code: {parent_code}" if parent_code else "🏁 Root Level Classification"

        system_prompt = """You are an expert HS (Harmonized System) code classification specialist.

Your task is to select the BEST HS code from a ranked list of candidates and provide detailed reasoning.

You must:
1. Analyze each candidate's relevance to the product
2. Consider trade classification principles and customs practices
3. Select the MOST SPECIFIC and ACCURATE code
4. Provide detailed justification for your selection
5. Assign a confidence score from 0.0 to 1.0

Key principles:
- More specific matches are preferred over general ones
- Consider the product's material, function, and intended use
- Follow official HS classification rules and notes
- Consider commercial and trade implications"""

        candidates_text = "\n".join([
            f"• Code: {c['code']} | Score: {c['relevance_score']:.2f} | {c['description']}"
            for c in candidate_dicts
        ])

        user_prompt = f"""[FINAL SELECTION - Level {level.value}] Select the best HS code from ranked candidates

🎯 CLASSIFICATION TASK: {level_names[level.value]} Level ({level.value}-digit codes)
📦 Product: "{product_description}"
{parent_context}

🏆 TOP RANKED CANDIDATES:
{candidates_text}

✅ Select the BEST code and provide:
1. Selected HS code
2. Confidence score (0.0-1.0)
3. Detailed reasoning for your choice

Choose the most specific and accurate code that best represents this product for trade classification purposes."""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]

        try:
            result = await self.selection_model.ainvoke(messages)

            # Convert candidate_dicts to HSCandidate objects
            candidates = [
                HSCandidate(
                    code=c['code'],
                    description=c['description'],
                    relevance_score=c['relevance_score'],
                    justification=f"Candidate with score {c['relevance_score']:.2f}"
                )
                for c in candidate_dicts
            ]

            return ClassificationResult(
                level=level,
                product_description=product_description,
                candidates=candidates,
                selected_code=result.selected_code,
                confidence=result.confidence,
                reasoning=result.reasoning
            )

        except Exception as e:
            # Fallback: select first candidate if available
            print(f"Warning: Selection failed, using fallback: {e}")
            if candidate_dicts:
                first_candidate = candidate_dicts[0]
                
                # Convert candidate_dicts to HSCandidate objects for fallback
                candidates = [
                    HSCandidate(
                        code=c['code'],
                        description=c['description'],
                        relevance_score=c.get('relevance_score', 0.5),
                        justification=f"Fallback candidate with score {c.get('relevance_score', 0.5):.2f}"
                    )
                    for c in candidate_dicts
                ]
                
                return ClassificationResult(
                    level=level,
                    product_description=product_description,
                    candidates=candidates,
                    selected_code=first_candidate["code"],
                    confidence=0.5,
                    reasoning=f"Fallback selection due to error: {e}"
                )
            else:
                # No candidates available - return a default error result
                print(f"Error: No candidates available for classification")
                return ClassificationResult(
                    level=level,
                    product_description=product_description,
                    candidates=[],
                    selected_code="0000.00",  # Default error code
                    confidence=0.0,
                    reasoning=f"No candidates found for classification. Error: {e}"
                )

    # =============================================================================
    # HELPER METHODS - Used by graph nodes
    # =============================================================================

    async def _llm_initial_ranking(
        self,
        product_description: str,
        codes_dict: Dict,
        level: ClassificationLevel,
        parent_code: str = None,
        top_k: int = 10
    ) -> List[tuple]:
        """Use LLM to do initial ranking of ALL codes and return top candidates."""

        # Prepare all codes for LLM evaluation
        all_codes_list = [
            {
                "code": code,
                "description": hs_code.description,
                "examples": self.data_loader.get_examples_for_code(code)[:3] if level == ClassificationLevel.SUBHEADING else []
            }
            for code, hs_code in codes_dict.items()
        ]

        # Create initial ranking prompt
        level_names = {"2": "CHAPTER", "4": "HEADING", "6": "SUBHEADING"}
        parent_context = f"🔗 Under Parent Code: {parent_code}" if parent_code else "🏁 Root Level Classification"

        system_prompt = """You are an expert HS (Harmonized System) code classification specialist.

Your task is to rank HS code candidates based on their relevance to a given product description.

For each candidate, you must:
1. Analyze how well the HS code description matches the product
2. Consider the specificity and accuracy of the match
3. Assign a relevance score from 0.0 to 1.0 (where 1.0 is perfect match)
4. Provide detailed justification for the score

Key principles:
- More specific matches should score higher than general ones
- Consider the intended use, material, and function of the product
- If multiple codes could apply, prefer the most specific one
- Consider trade regulations and customs classification practices

Return the candidates ranked by relevance score (highest first) with detailed justifications."""

        user_prompt = f"""[INITIAL RANKING - Level {level.value}] Evaluate ALL {len(all_codes_list)} available HS codes and find the best matches

🎯 CLASSIFICATION TASK: {level_names[level.value]} Level ({level.value}-digit codes)
📦 Product: "{product_description}"
{parent_context}

🔍 INSTRUCTIONS:
1. Analyze how well each HS code matches the product
2. Consider the specificity, accuracy, and trade classification principles
3. Select the top {top_k} most relevant codes
4. Rank them by relevance (most relevant first)
5. Assign relevance scores from 0.0 to 1.0

📊 CODES TO EVALUATE ({len(all_codes_list)} total):
{chr(10).join([f"{i+1}. Code: {c['code']} - {c['description']}" + (f" | Examples: {', '.join(c['examples'])}" if c['examples'] else "") for i, c in enumerate(all_codes_list)])}

✅ Return ONLY the top {top_k} codes ranked by relevance."""

        # Get initial ranking from LLM using structured output
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]

        try:
            result = await self.ranking_model.ainvoke(messages)

            # Convert to our tuple format
            candidates = []
            for ranked_candidate in result.ranked_candidates:
                code = ranked_candidate.code
                if code and code in codes_dict:
                    hs_code = codes_dict[code]
                    score = ranked_candidate.relevance_score
                    candidates.append((code, hs_code, score))

        except Exception as e:
            # Fallback: just take the first few codes
            print(f"Warning: Structured output failed, using fallback: {e}")
            all_codes = list(codes_dict.items())[:top_k]
            candidates = []
            for i, (code, hs_code) in enumerate(all_codes):
                score = max(0.1, 0.8 - (i * 0.1))  # Decreasing scores
                candidates.append((code, hs_code, score))

        return candidates[:top_k]

    # =============================================================================
    # MAIN PUBLIC API - Classification entry point
    # =============================================================================

    async def classify_hierarchical(
        self,
        product_description: str,
        top_k: int = 10
    ) -> Dict[str, Any]:
        """Perform complete hierarchical HS classification using LangGraph."""

        # Initial state
        initial_state = {
            "product_description": product_description,
            "top_k": top_k,
            "current_level": None,
            "chapter_candidates": None,
            "chapter_result": None,
            "heading_candidates": None,
            "heading_result": None,
            "subheading_candidates": None,
            "subheading_result": None,
            "final_code": None,
            "overall_confidence": None,
            "processing_time": None,
            "error": None,
            "trace_context": None
        }

        # Prepare config for graph execution with Langfuse v3 metadata
        config = {}
        if self.langfuse_handler is not None:
            config["callbacks"] = [self.langfuse_handler]
            config["metadata"] = {
                "langfuse_session_id": f"hs-classification-{hash(product_description)}",
                "langfuse_tags": ["hs-classification", "hierarchical", "langgraph"],
                "langfuse_user_id": "hs-agent-system"
            }
        
        # Run the classification graph
        try:
            final_state = await self.classification_graph.ainvoke(initial_state, config=config)
        except Exception as e:
            logger.error(f"Graph execution failed: {e}")
            raise AgentError(
                message=f"Classification graph execution failed: {str(e)}",
                error_code="GRAPH_EXECUTION_FAILED",
                details={"product_description": product_description, "original_error": str(e)},
                cause=e
            )

        # Format results to match original agent interface
        results = {
            "chapter": final_state["chapter_result"],
            "heading": final_state["heading_result"],
            "subheading": final_state["subheading_result"],
            "final_code": final_state["final_code"],
            "overall_confidence": final_state["overall_confidence"]
        }

        # Flush Langfuse events to ensure they are sent (important for short-lived applications)
        if settings.langfuse_enabled:
            try:
                langfuse_client = get_client()
                langfuse_client.flush()
                logger.debug("✅ Langfuse events flushed")
            except Exception as e:
                logger.warning(f"⚠️ Failed to flush Langfuse events: {e}")

        return results

    # =============================================================================
    # MULTI-CHOICE LOOPING GRAPH IMPLEMENTATION
    # =============================================================================

    def _build_multi_choice_graph(self):
        """Build the simplified multi-choice classification StateGraph with list-based looping."""
        try:
            # Create the simplified multi-choice workflow graph
            workflow = StateGraph(HSMultiChoiceState)

            # Add nodes for simplified multi-choice classification
            workflow.add_node("rank_chapter_candidates", self._rank_chapters_multi)
            workflow.add_node("select_multiple_chapters", self._select_multiple_chapters_simple)

            # Chapter processing - loop through all selected chapters
            workflow.add_node("process_all_chapters", self._process_all_chapters)

            # Heading processing - loop through all collected headings
            workflow.add_node("process_all_headings", self._process_all_headings)

            # Final aggregation
            workflow.add_node("aggregate_all_results", self._aggregate_all_results)

            # Simple sequential flow - no complex routing!
            workflow.add_edge(START, "rank_chapter_candidates")
            workflow.add_edge("rank_chapter_candidates", "select_multiple_chapters")
            workflow.add_edge("select_multiple_chapters", "process_all_chapters")
            workflow.add_edge("process_all_chapters", "process_all_headings")
            workflow.add_edge("process_all_headings", "aggregate_all_results")
            workflow.add_edge("aggregate_all_results", END)

            # Compile the graph
            compiled_graph = workflow.compile()
            logger.info("✅ Simplified multi-choice classification graph compiled successfully")
            return compiled_graph

        except Exception as e:
            logger.error(f"Failed to build simplified multi-choice classification graph: {e}")
            raise

    # =============================================================================
    # SIMPLIFIED MULTI-CHOICE GRAPH NODES
    # =============================================================================

    async def _rank_chapters_multi(self, state: HSMultiChoiceState) -> HSMultiChoiceState:
        """STEP 1: Broad initial ranking of chapter candidates with high K."""
        initial_k = state["initial_ranking_k"]
        logger.info(f"🔍 STEP 1: Broad initial ranking of chapter candidates with K={initial_k}")

        codes_dict = self.data_loader.codes_2digit
        candidates = await self._llm_initial_ranking(
            state["product_description"],
            codes_dict,
            ClassificationLevel.CHAPTER,
            None,
            initial_k  # Use high K for broad initial ranking
        )

        candidate_dicts = [
            {
                "code": code,
                "description": hs_code.description,
                "relevance_score": score
            }
            for code, hs_code, score in candidates
        ]

        logger.info(f"✅ Broad ranking complete: {len(candidate_dicts)} chapter candidates (top {initial_k})")
        return {
            **state,
            "chapter_candidates": candidate_dicts
        }

    async def _select_multiple_chapters_simple(self, state: HSMultiChoiceState) -> HSMultiChoiceState:
        """STEP 2: Refined selection from broadly ranked candidates (1 to max_n range)."""
        candidates = state.get("chapter_candidates", [])
        max_n = state["max_selections_per_level"]
        logger.info(f"🎯 STEP 2: Refined selection from {len(candidates)} candidates (range: 1 to {max_n})")

        result = await self._llm_multi_selection(
            state["product_description"],
            candidates,
            ClassificationLevel.CHAPTER,
            max_n,  # This is the maximum, LLM can choose 1 to max_n
            state["min_confidence_threshold"]
        )

        # Filter selected chapters that meet confidence threshold
        high_confidence_chapters = [
            code for code, conf in zip(result.selected_codes, result.individual_confidences)
            if conf >= state["min_confidence_threshold"]
        ]

        # Ensure we have at least 1 selection if any candidates meet threshold
        if not high_confidence_chapters and result.selected_codes:
            # Take the highest confidence selection even if below threshold
            best_idx = result.individual_confidences.index(max(result.individual_confidences))
            high_confidence_chapters = [result.selected_codes[best_idx]]
            logger.warning(f"No chapters met threshold, using best: {high_confidence_chapters[0]}")

        logger.info(f"✅ Refined selection: {len(high_confidence_chapters)} chapters: {high_confidence_chapters}")

        return {
            **state,
            "selected_chapters": high_confidence_chapters,
            "chapters_to_process": high_confidence_chapters.copy()  # Initialize processing list
        }

    async def _process_single_chapter(self, chapter_code: str, product_description: str, initial_ranking_k: int, max_selections: int, min_confidence: float) -> tuple:
        """Process a single chapter to get its headings using two-step approach."""
        logger.info(f"  🧵 Processing chapter: {chapter_code} (two-step ranking)")

        # Get all headings under this chapter
        codes_dict = {
            code: hs_code for code, hs_code in self.data_loader.codes_4digit.items()
            if code.startswith(chapter_code)
        }

        if not codes_dict:
            logger.warning(f"    No headings found for chapter {chapter_code}")
            return chapter_code, []

        # STEP 1: Broad initial ranking with high K
        candidates = await self._llm_initial_ranking(
            product_description,
            codes_dict,
            ClassificationLevel.HEADING,
            chapter_code,
            initial_ranking_k  # Use high K for broad coverage
        )

        candidate_dicts = [
            {
                "code": code,
                "description": hs_code.description,
                "relevance_score": score
            }
            for code, hs_code, score in candidates
        ]

        # STEP 2: Refined selection (1 to max_n range)
        result = await self._llm_multi_selection(
            product_description,
            candidate_dicts,
            ClassificationLevel.HEADING,
            max_selections,  # Max selections (LLM chooses 1 to max_n)
            min_confidence,
            chapter_code
        )

        # Collect selected headings
        selected_headings = [
            code for code, conf in zip(result.selected_codes, result.individual_confidences)
            if conf >= min_confidence
        ]

        # Ensure at least 1 selection per chapter
        if not selected_headings and result.selected_codes:
            best_idx = result.individual_confidences.index(max(result.individual_confidences))
            selected_headings = [result.selected_codes[best_idx]]
            logger.warning(f"    Chapter {chapter_code}: using best heading despite low confidence")

        logger.info(f"    ✅ Chapter {chapter_code}: {len(selected_headings)} headings from {len(candidate_dicts)} candidates: {selected_headings}")
        return chapter_code, selected_headings

    async def _process_all_chapters(self, state: HSMultiChoiceState) -> HSMultiChoiceState:
        """Process all selected chapters to collect headings using concurrent processing."""
        chapters_to_process = state.get("chapters_to_process", [])
        logger.info(f"🔄 Processing {len(chapters_to_process)} chapters CONCURRENTLY to collect headings")

        all_headings_to_process = []
        heading_parent_mapping = {}  # Track which chapter each heading belongs to

        # Process all chapters concurrently
        tasks = []
        for chapter_code in chapters_to_process:
            task = self._process_single_chapter(
                chapter_code,
                state["product_description"],
                state["initial_ranking_k"],  # Use high K for broad ranking
                state["max_selections_per_level"],
                state["min_confidence_threshold"]
            )
            tasks.append(task)

        # Wait for all chapters to be processed
        logger.info(f"⚡ Starting concurrent processing of {len(tasks)} chapters...")
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Collect results
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Chapter processing failed: {result}")
                continue

            chapter_code, selected_headings = result

            # Add to processing list and track parent chapter
            for heading_code in selected_headings:
                all_headings_to_process.append(heading_code)
                heading_parent_mapping[heading_code] = chapter_code

        logger.info(f"✅ Collected {len(all_headings_to_process)} headings total: {all_headings_to_process}")

        return {
            **state,
            "headings_to_process": all_headings_to_process,
            "heading_parent_mapping": heading_parent_mapping  # Track chapter relationships
        }

    async def _process_single_heading(self, heading_code: str, chapter_code: str, product_description: str, initial_ranking_k: int, max_selections: int, min_confidence: float) -> List[ClassificationPath]:
        """Process a single heading to get its classification paths using two-step approach."""
        logger.info(f"  🧵 Processing heading: {heading_code} (from chapter {chapter_code}, two-step ranking)")

        # Get all subheadings under this heading
        codes_dict = {
            code: hs_code for code, hs_code in self.data_loader.codes_6digit.items()
            if code.startswith(heading_code)
        }

        if not codes_dict:
            # Create a fallback candidate using the parent heading code
            candidate_dicts = [{
                "code": heading_code + ".00",
                "description": f"General subheading under {heading_code}",
                "relevance_score": 0.5
            }]
            logger.info(f"    Using fallback subheading for {heading_code}")
        else:
            # STEP 1: Broad initial ranking with high K
            candidates = await self._llm_initial_ranking(
                product_description,
                codes_dict,
                ClassificationLevel.SUBHEADING,
                heading_code,
                initial_ranking_k  # Use high K for broad coverage
            )

            candidate_dicts = [
                {
                    "code": code,
                    "description": hs_code.description,
                    "relevance_score": score
                }
                for code, hs_code, score in candidates
            ]

        # STEP 2: Refined selection (1 to max_n range)
        result = await self._llm_multi_selection(
            product_description,
            candidate_dicts,
            ClassificationLevel.SUBHEADING,
            max_selections,  # Max selections (LLM chooses 1 to max_n)
            min_confidence,
            heading_code
        )

        # Create classification paths for each selected subheading
        paths = []
        for subheading_code, confidence in zip(result.selected_codes, result.individual_confidences):
            if confidence >= min_confidence:
                path = ClassificationPath(
                    chapter_code=chapter_code,
                    heading_code=heading_code,
                    subheading_code=subheading_code,
                    path_confidence=confidence,
                    chapter_reasoning=f"Two-step selection for chapter {chapter_code}",
                    heading_reasoning=f"Two-step selection for heading {heading_code}",
                    subheading_reasoning=result.reasoning
                )
                paths.append(path)

        # Ensure at least 1 path per heading
        if not paths and result.selected_codes:
            best_idx = result.individual_confidences.index(max(result.individual_confidences))
            best_subheading = result.selected_codes[best_idx]
            best_confidence = result.individual_confidences[best_idx]

            path = ClassificationPath(
                chapter_code=chapter_code,
                heading_code=heading_code,
                subheading_code=best_subheading,
                path_confidence=best_confidence,
                chapter_reasoning=f"Two-step selection for chapter {chapter_code}",
                heading_reasoning=f"Two-step selection for heading {heading_code}",
                subheading_reasoning=f"Best option despite low confidence: {result.reasoning}"
            )
            paths.append(path)
            logger.warning(f"    Heading {heading_code}: using best path despite low confidence")

        logger.info(f"    ✅ Heading {heading_code}: {len(paths)} paths from {len(candidate_dicts)} candidates")
        return paths

    async def _process_all_headings(self, state: HSMultiChoiceState) -> HSMultiChoiceState:
        """Process all selected headings to create final classification paths using concurrent processing."""
        headings_to_process = state.get("headings_to_process", [])
        heading_parent_mapping = state.get("heading_parent_mapping", {})
        logger.info(f"🔄 Processing {len(headings_to_process)} headings CONCURRENTLY to create classification paths")

        # Process all headings concurrently
        tasks = []
        for heading_code in headings_to_process:
            chapter_code = heading_parent_mapping.get(heading_code)
            task = self._process_single_heading(
                heading_code,
                chapter_code,
                state["product_description"],
                state["initial_ranking_k"],  # Use high K for broad ranking
                state["max_selections_per_level"],
                state["min_confidence_threshold"]
            )
            tasks.append(task)

        # Wait for all headings to be processed
        logger.info(f"⚡ Starting concurrent processing of {len(tasks)} headings...")
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Collect all classification paths
        all_classification_paths = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Heading processing failed: {result}")
                continue

            # result is a list of ClassificationPath objects
            all_classification_paths.extend(result)

        logger.info(f"✅ Created {len(all_classification_paths)} total classification paths")

        return {
            **state,
            "all_classification_paths": all_classification_paths
        }


    async def _aggregate_all_results(self, state: HSMultiChoiceState) -> HSMultiChoiceState:
        """Aggregate all classification paths and calculate final metrics."""
        all_paths = state.get("all_classification_paths", [])

        if not all_paths:
            logger.warning("No classification paths found")
            return {
                **state,
                "overall_confidence": 0.0,
                "processing_stats": {"total_paths": 0}
            }

        # Calculate overall confidence as average of all path confidences
        overall_confidence = sum(path.path_confidence for path in all_paths) / len(all_paths)

        # Calculate processing statistics
        processing_stats = {
            "total_paths": len(all_paths),
            "unique_chapters": len(set(path.chapter_code for path in all_paths)),
            "unique_headings": len(set(path.heading_code for path in all_paths)),
            "unique_subheadings": len(set(path.subheading_code for path in all_paths))
        }

        logger.info(f"🎯 Final aggregation: {processing_stats}")

        return {
            **state,
            "overall_confidence": overall_confidence,
            "processing_stats": processing_stats
        }

    # =============================================================================
    # MULTI-CHOICE LLM HELPER METHODS
    # =============================================================================

    async def _llm_multi_selection(
        self,
        product_description: str,
        candidate_dicts: List[Dict],
        level: ClassificationLevel,
        max_selections: int,
        min_confidence: float,
        parent_code: str = None
    ) -> MultiSelectionOutput:
        """Use LLM for multi-choice selection with detailed reasoning."""

        level_names = {"2": "CHAPTER", "4": "HEADING", "6": "SUBHEADING"}
        parent_context = f"🔗 Under Parent Code: {parent_code}" if parent_code else "🏁 Root Level Classification"

        system_prompt = """You are an expert HS (Harmonized System) code classification specialist.

Your task is to select MULTIPLE relevant HS codes from a ranked list of candidates.

You must:
1. Analyze each candidate's relevance to the product
2. Select between 1 and the maximum allowed codes (flexible range)
3. Choose only codes that meet the minimum confidence threshold
4. Provide individual confidence scores for each selected code
5. Provide detailed justification for your selections

SELECTION STRATEGY:
- Start with the most relevant candidates (highest scores)
- You can select 1, 2, 3, or up to the maximum - be flexible
- Choose MORE codes for ambiguous products that could fit multiple categories
- Choose FEWER codes for products with clear, specific matches
- All selected codes should be above the confidence threshold
- Consider trade classification principles and customs practices"""

        candidates_text = "\n".join([
            f"• Code: {c['code']} | Score: {c['relevance_score']:.2f} | {c['description']}"
            for c in candidate_dicts
        ])

        user_prompt = f"""[TWO-STEP MULTI-SELECTION - Level {level.value}] Refined selection from broadly ranked candidates

🎯 CLASSIFICATION TASK: {level_names[level.value]} Level ({level.value}-digit codes)
📦 Product: "{product_description}"
{parent_context}

🔄 TWO-STEP PROCESS:
• STEP 1 (Complete): Broad initial ranking has identified top candidates
• STEP 2 (Current): Refined selection from these candidates

📊 SELECTION CONSTRAINTS:
• Selection range: 1 to {max_selections} codes (be flexible!)
• Minimum confidence: {min_confidence:.2f}
• Quality over quantity - choose the most relevant codes

🏆 BROADLY RANKED CANDIDATES (Step 1 Results):
{candidates_text}

✅ From these candidates, select the BEST ones and provide:
1. Selected HS codes (1 to {max_selections} codes)
2. Individual confidence scores for each (0.0-1.0)
3. Overall confidence for the selection set
4. Detailed reasoning for your refined selection

GUIDANCE: Choose fewer codes for clear matches, more codes for ambiguous products that could fit multiple categories."""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]

        try:
            result = await self.multi_selection_model.ainvoke(messages)
            return result

        except Exception as e:
            # Fallback: select the top candidate if available
            logger.warning(f"Multi-selection failed, using fallback: {e}")
            if candidate_dicts:
                first_candidate = candidate_dicts[0]
                return MultiSelectionOutput(
                    selected_codes=[first_candidate["code"]],
                    individual_confidences=[0.5],
                    overall_confidence=0.5,
                    reasoning=f"Fallback selection due to error: {e}"
                )
            else:
                return MultiSelectionOutput(
                    selected_codes=["0000.00"],
                    individual_confidences=[0.0],
                    overall_confidence=0.0,
                    reasoning=f"No candidates found. Error: {e}"
                )

    # =============================================================================
    # MULTI-CHOICE PUBLIC API
    # =============================================================================

    async def classify_multi_choice(
        self,
        product_description: str,
        initial_ranking_k: int = 20,  # High K for broad initial ranking
        max_selections_per_level: int = 3,  # Max selections (1 to max_n range)
        min_confidence_threshold: float = 0.6
    ) -> Dict[str, Any]:
        """Perform multi-choice hierarchical HS classification with looping."""

        # Initial state for two-step ranking approach
        initial_state = {
            "product_description": product_description,
            "initial_ranking_k": initial_ranking_k,  # High K for broad initial ranking
            "max_selections_per_level": max_selections_per_level,
            "min_confidence_threshold": min_confidence_threshold,
            "chapter_candidates": None,
            "selected_chapters": [],
            "chapters_to_process": [],
            "headings_to_process": [],  # Simplified: flat list of headings
            "heading_parent_mapping": {},  # Track chapter relationships
            "subheading_candidates": {},  # Keep for compatibility
            "current_processing_chapter": None,  # Keep for compatibility
            "current_processing_heading": None,  # Keep for compatibility
            "all_classification_paths": [],
            "processing_stats": {},
            "overall_confidence": None,
            "error": None,
            "trace_context": None
        }

        # Prepare config for graph execution
        config = {}
        if self.langfuse_handler is not None:
            config["callbacks"] = [self.langfuse_handler]
            config["metadata"] = {
                "langfuse_session_id": f"hs-multi-classification-{hash(product_description)}",
                "langfuse_tags": ["hs-classification", "multi-choice", "hierarchical", "langgraph"],
                "langfuse_user_id": "hs-agent-system"
            }

        # Run the multi-choice classification graph
        try:
            final_state = await self.multi_choice_graph.ainvoke(initial_state, config=config)
        except Exception as e:
            logger.error(f"Multi-choice graph execution failed: {e}")
            raise AgentError(
                message=f"Multi-choice classification graph execution failed: {str(e)}",
                error_code="MULTI_CHOICE_GRAPH_EXECUTION_FAILED",
                details={"product_description": product_description, "original_error": str(e)},
                cause=e
            )

        # Format results
        results = {
            "all_classification_paths": final_state["all_classification_paths"],
            "processing_stats": final_state["processing_stats"],
            "overall_confidence": final_state["overall_confidence"],
            "selected_chapters": final_state["selected_chapters"],
            "total_paths": len(final_state["all_classification_paths"])
        }

        # Flush Langfuse events
        if settings.langfuse_enabled:
            try:
                langfuse_client = get_client()
                langfuse_client.flush()
                logger.debug("✅ Langfuse events flushed")
            except Exception as e:
                logger.warning(f"⚠️ Failed to flush Langfuse events: {e}")

        return results