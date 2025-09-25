"""LangGraph agents for HS code classification."""

# Standard library imports
from typing import List, Dict, Any, Optional

# Third-party imports
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_google_vertexai import ChatVertexAI
from langfuse import Langfuse, get_client
from langfuse.langchain import CallbackHandler
from langgraph.graph import StateGraph, START, END

# Local imports
from hs_agent.agents.langgraph.models import (
    HSClassificationState,
    ClassificationLevel,
    HSCandidate,
    ClassificationResult,
    RankedCandidate,
    RankingOutput,
    SelectionOutput
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

        # Build the main hierarchical classification graph
        self.classification_graph = self._build_classification_graph()

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