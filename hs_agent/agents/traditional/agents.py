"""Pydantic AI agents for HS code classification."""

import os
from typing import List, Dict, Any, Tuple, Optional
from dotenv import load_dotenv
from pydantic_ai import Agent
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider
from langfuse import Langfuse

from hs_agent.core.models import (
    HSCandidate,
    RankingRequest,
    RankingResponse,
    ClassificationLevel,
    ClassificationResult
)
from hs_agent.config import settings
from hs_agent.core.logging import get_logger
from hs_agent.core.exceptions import AgentError, ExternalServiceError
from hs_agent.core.data_loader import HSDataLoader
from hs_agent.core.models.entities import HSCode

# Initialize logger
logger = get_logger(__name__)


class HSClassificationAgent:
    """Main HS classification agent that handles the hierarchical classification process."""

    def __init__(self, data_loader: HSDataLoader, model_name: Optional[str] = None):
        self.data_loader = data_loader
        
        # Use configured model name or default
        self.model_name = model_name or settings.default_model_name
        
        try:
            # Set up Vertex AI provider
            provider = GoogleProvider(vertexai=True)
            self.model = GoogleModel(self.model_name, provider=provider)
            
            logger.info(
                "🤖 Traditional agent initialized",
                model_name=self.model_name,
                langfuse_enabled=settings.langfuse_enabled
            )
            
        except Exception as e:
            error_msg = f"Failed to initialize traditional agent: {str(e)}"
            logger.error(error_msg, model_name=self.model_name)
            raise AgentError(
                message=error_msg,
                error_code="AGENT_INITIALIZATION_FAILED",
                details={"model_name": self.model_name, "original_error": str(e)},
                cause=e
            )

        # Initialize Langfuse client if enabled
        if settings.langfuse_enabled:
            try:
                self.langfuse = Langfuse(
                    secret_key=settings.langfuse_secret_key,
                    public_key=settings.langfuse_public_key,
                    host=settings.langfuse_host
                )
                
                if self.langfuse.auth_check():
                    logger.info("✅ Langfuse client authenticated")
                else:
                    logger.warning("⚠️ Langfuse authentication failed")
                    
            except Exception as e:
                logger.warning(f"⚠️ Langfuse connection warning: {e}")
                self.langfuse = None
        else:
            self.langfuse = None
            logger.info("Langfuse observability disabled")

        # Enable Pydantic AI instrumentation for automatic tracing
        Agent.instrument_all()

        # Initialize specialized agents with instrumentation enabled
        self.ranking_agent = Agent(
            model=self.model,
            output_type=RankingResponse,
            system_prompt=self._get_ranking_system_prompt(),
            instrument=True
        )
        self.ranking_agent.name = "HS-Code-Initial-Ranker"

        self.selection_agent = Agent(
            model=self.model,
            output_type=ClassificationResult,
            system_prompt=self._get_selection_system_prompt(),
            instrument=True
        )
        self.selection_agent.name = "HS-Code-Final-Selector"

    def _get_ranking_system_prompt(self) -> str:
        """System prompt for the ranking agent."""
        return """You are an expert HS (Harmonized System) code classification specialist.

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

    def _get_selection_system_prompt(self) -> str:
        """System prompt for the selection agent."""
        return """You are an expert HS code classifier making final selection decisions.

You will receive ranked candidates for HS code classification. Your task is to:
1. Review the ranked candidates and their justifications
2. Select the most appropriate HS code
3. Assign a confidence score (0.0 to 1.0)
4. Provide clear reasoning for your final selection

Consider:
- The quality and specificity of matches
- Customs classification best practices
- Any ambiguities or edge cases
- The confidence level based on available information

Make a definitive selection even if multiple codes seem reasonable."""

    async def classify_at_level(
        self,
        product_description: str,
        level: ClassificationLevel,
        parent_code: str = None,
        top_k: int = 10
    ) -> ClassificationResult:
        """Classify a product at a specific HS level."""

        # Create a level-specific span as child of main trace
        level_names = {"2": "CHAPTER", "4": "HEADING", "6": "SUBHEADING"}
        with self.langfuse.start_as_current_span(
            name=f"🎯 {level.value}-Digit {level_names[level.value]} Classification",
            input={
                "product_description": product_description,
                "level": f"{level.value}-digit ({level_names[level.value]})",
                "parent_code": parent_code,
                "top_k": top_k
            },
            metadata={
                "classification_level": level.value,
                "level_name": level_names[level.value],
                "has_parent": parent_code is not None
            }
        ) as level_span:

            # Get candidate codes for this level using LLM initial ranking
            candidates = await self._get_candidates(product_description, level, parent_code, top_k)

            if not candidates:
                raise ValueError(f"No candidates found for level {level}")

            # Prepare candidates for ranking
            candidate_dicts = [
                {
                    "code": code,
                    "description": hs_code.description,
                    "examples": self.data_loader.get_examples_for_code(code) if level == ClassificationLevel.SUBHEADING else []
                }
                for code, hs_code, _ in candidates
            ]

            # Temporarily rename agents to include level context for this specific call
            original_ranking_name = self.ranking_agent.name if hasattr(self.ranking_agent, 'name') else None
            original_selection_name = self.selection_agent.name if hasattr(self.selection_agent, 'name') else None

            level_int = int(level.value)
            self.ranking_agent.name = f"HS-{level_int}digit-{level_names[level.value]}-Ranker"
            self.selection_agent.name = f"HS-{level_int}digit-{level_names[level.value]}-Selector"

            # Rank candidates using AI
            parent_context = f"🔗 Parent Code: {parent_code}" if parent_code else "🏁 Root Level Classification"
            ranking_prompt = f"""[DETAILED RANKING - Level {level.value}] Rank these HS code candidates for the product: '{product_description}'

🎯 CLASSIFICATION TASK: {level.name} Level ({level.value}-digit codes)
📦 Product Description: {product_description}
{parent_context}

📋 Candidates to rank:
{chr(10).join([f"{i+1}. Code: {c['code']}, Description: {c['description']}" for i, c in enumerate(candidate_dicts)])}

For each candidate, provide:
1. A relevance score from 0.0 to 1.0
2. Detailed justification for the score

Return them ranked by relevance (highest first)."""

            ranking_result = await self.ranking_agent.run(ranking_prompt)

            # Use the ranked candidates to reorder our list
            ranked_candidates = ranking_result.output.ranked_candidates

            # Create a mapping of codes to their ranking information
            ranking_map = {candidate.code: candidate for candidate in ranked_candidates}

            # Reorder candidate_dicts based on the AI ranking
            reordered_candidates = []
            for ranked_candidate in ranked_candidates:
                # Find the matching candidate from our original list
                for orig_candidate in candidate_dicts:
                    if orig_candidate['code'] == ranked_candidate.code:
                        reordered_candidates.append(orig_candidate)
                        break

            # Add any candidates that weren't ranked (fallback)
            ranked_codes = {rc.code for rc in ranked_candidates}
            for orig_candidate in candidate_dicts:
                if orig_candidate['code'] not in ranked_codes:
                    reordered_candidates.append(orig_candidate)

            # Select final code using AI with properly ranked candidates
            parent_context = f"🔗 Parent Code: {parent_code}" if parent_code else "🏁 Root Level Classification"
            selection_prompt = f"""[FINAL SELECTION - Level {level.value}] Select the best HS code from these ranked candidates:

🎯 CLASSIFICATION TASK: {level.name} Level ({level.value}-digit codes)
📦 Product: {product_description}
{parent_context}

🏆 Ranked candidates (in order of relevance):
{chr(10).join([f"{i+1}. Code: {c['code']}, Description: {c['description']}" for i, c in enumerate(reordered_candidates)])}

🤔 AI Ranking Analysis:
{ranking_result.output.reasoning}

📊 Top candidate details:
{chr(10).join([f"Code {rc.code}: Score {rc.relevance_score:.2f} - {rc.justification}" for rc in ranked_candidates[:3]])}

✅ Make your final selection and provide confidence score and reasoning."""

            selection_result = await self.selection_agent.run(selection_prompt)

            # Restore original agent names
            if original_ranking_name is not None:
                self.ranking_agent.name = original_ranking_name
            if original_selection_name is not None:
                self.selection_agent.name = original_selection_name

            # Update the level span with the final result
            level_span.update(
                output={
                    "selected_code": selection_result.output.selected_code,
                    "confidence": selection_result.output.confidence,
                    "reasoning": selection_result.output.reasoning,
                    "candidates_evaluated": len(candidates)
                }
            )

            return selection_result.output

    async def _get_candidates(
        self,
        product_description: str,
        level: ClassificationLevel,
        parent_code: str = None,
        top_k: int = 10
    ) -> List[tuple]:
        """Get candidate HS codes using LLM for initial ranking."""

        level_int = int(level.value)

        if parent_code:
            # Filter codes that start with parent code
            all_codes = self.data_loader.get_codes_by_level(level_int)
            filtered_codes = {
                code: hs_code for code, hs_code in all_codes.items()
                if code.startswith(parent_code)
            }
        else:
            # Use all codes at this level
            filtered_codes = self.data_loader.get_codes_by_level(level_int)

        # Let LLM do the initial ranking of ALL codes
        candidates = await self._llm_initial_ranking(
            product_description, filtered_codes, level, parent_code, top_k
        )

        return candidates

    async def _llm_initial_ranking(
        self,
        product_description: str,
        codes_dict: Dict,
        level: ClassificationLevel,
        parent_code: str = None,
        top_k: int = 10
    ) -> List[tuple]:
        """Use LLM to do initial ranking of ALL codes and return top candidates."""

        # Create a span for initial ranking step as nested span
        with self.langfuse.start_as_current_span(
            name=f"🔍 Initial LLM Ranking ({level.value}-digit)",
            input={
                "product_description": product_description,
                "level": level.value,
                "total_codes": len(codes_dict),
                "top_k": top_k
            },
            metadata={
                "step": "initial_ranking",
                "codes_available": len(codes_dict)
            }
        ) as span:

            # Prepare all codes for LLM evaluation
            all_codes_list = [
                {
                    "code": code,
                    "description": hs_code.description,
                    "examples": self.data_loader.get_examples_for_code(code)[:3] if level == ClassificationLevel.SUBHEADING else []
                }
                for code, hs_code in codes_dict.items()
            ]

            # Temporarily rename ranking agent to include level context
            original_name = self.ranking_agent.name if hasattr(self.ranking_agent, 'name') else None
            level_names = {"2": "CHAPTER", "4": "HEADING", "6": "SUBHEADING"}
            level_int = int(level.value)
            self.ranking_agent.name = f"HS-{level_int}digit-{level_names[level.value]}-InitialRanker"

            # Create initial ranking prompt
            parent_context = f"🔗 Under Parent Code: {parent_code}" if parent_code else "🏁 Root Level Classification"
            initial_ranking_prompt = f"""[INITIAL RANKING - Level {level.value}] You are an expert HS (Harmonized System) code classifier.

🎯 CLASSIFICATION TASK: {level.name} Level ({level.value}-digit codes)
📦 Product: "{product_description}"
{parent_context}

📋 TASK: Evaluate ALL {len(all_codes_list)} available HS codes and find the best matches

🔍 INSTRUCTIONS:
1. Analyze how well each HS code matches the product
2. Consider the specificity, accuracy, and trade classification principles
3. Select the top {top_k} most relevant codes
4. Rank them by relevance (most relevant first)
5. Assign relevance scores from 0.0 to 1.0

📊 CODES TO EVALUATE ({len(all_codes_list)} total):
{chr(10).join([f"{i+1}. Code: {c['code']} - {c['description']}" + (f" | Examples: {', '.join(c['examples'])}" if c['examples'] else "") for i, c in enumerate(all_codes_list)])}

✅ Return ONLY the top {top_k} codes ranked by relevance."""

            # Get initial ranking from LLM
            initial_result = await self.ranking_agent.run(initial_ranking_prompt)

            # Restore original agent name
            if original_name is not None:
                self.ranking_agent.name = original_name

            # Convert LLM ranking back to our tuple format
            candidates = []
            for ranked_candidate in initial_result.output.ranked_candidates:
                if ranked_candidate.code in codes_dict:
                    hs_code = codes_dict[ranked_candidate.code]
                    candidates.append((ranked_candidate.code, hs_code, ranked_candidate.relevance_score))

            # Update span with results
            span.update(
                output={
                    "selected_candidates": [c[0] for c in candidates[:top_k]],
                    "scores": [c[2] for c in candidates[:top_k]],
                    "reasoning": initial_result.output.reasoning if hasattr(initial_result.output, 'reasoning') else None
                }
            )

            return candidates[:top_k]


    async def classify_hierarchical(
        self,
        product_description: str,
        top_k: int = 10
    ) -> Dict[str, Any]:
        """Perform complete hierarchical HS classification."""

        results = {}

        # Step 1: 2-digit chapter classification
        chapter_result = await self.classify_at_level(
            product_description,
            ClassificationLevel.CHAPTER,
            top_k=top_k
        )
        results["chapter"] = chapter_result

        # Step 2: 4-digit heading classification
        heading_result = await self.classify_at_level(
            product_description,
            ClassificationLevel.HEADING,
            parent_code=chapter_result.selected_code,
            top_k=top_k
        )
        results["heading"] = heading_result

        # Step 3: 6-digit subheading classification
        subheading_result = await self.classify_at_level(
            product_description,
            ClassificationLevel.SUBHEADING,
            parent_code=heading_result.selected_code,
            top_k=top_k
        )
        results["subheading"] = subheading_result

        # Calculate overall confidence
        overall_confidence = (
            chapter_result.confidence * 0.3 +
            heading_result.confidence * 0.3 +
            subheading_result.confidence * 0.4
        )

        results["final_code"] = subheading_result.selected_code
        results["overall_confidence"] = overall_confidence

        return results