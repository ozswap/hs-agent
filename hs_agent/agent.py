"""Simplified HS classification agent."""

from typing import Dict, Any, List, Optional
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_google_vertexai import ChatVertexAI
from hs_agent.models import (
    ClassificationLevel,
    RankingOutput,
    SelectionOutput,
    ClassificationResult,
    ClassificationResponse
)
from hs_agent.config.settings import settings
from hs_agent.data_loader import HSDataLoader


class HSAgent:
    """HS classification agent using hierarchical LLM approach."""

    def __init__(self, data_loader: HSDataLoader, model_name: Optional[str] = None):
        self.data_loader = data_loader
        self.model_name = model_name or settings.default_model_name

        # Initialize Langfuse client if enabled (SDK v3)
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

        # Initialize models with Langfuse callbacks if available
        callbacks = [self.langfuse_handler] if self.langfuse_handler else []
        self.model = ChatVertexAI(model=self.model_name, callbacks=callbacks)
        self.ranking_model = self.model.with_structured_output(RankingOutput)
        self.selection_model = self.model.with_structured_output(SelectionOutput)

    async def classify(self, product_description: str, top_k: int = 10) -> ClassificationResponse:
        """Classify a product to get its HS code."""
        import time

        # Wrap execution in Langfuse trace if enabled (SDK v3 pattern)
        if self.langfuse_handler:
            from langfuse import get_client
            langfuse = get_client()

            with langfuse.start_as_current_span(name="HS_Classification") as span:
                # Update trace with input
                span.update_trace(
                    input={"product_description": product_description, "top_k": top_k},
                    metadata={"model": self.model_name}
                )

                # Perform classification
                response = await self._perform_classification(product_description, top_k)

                # Update trace with output
                span.update_trace(
                    output={
                        "final_code": response.final_code,
                        "confidence": response.overall_confidence,
                        "chapter": response.chapter.selected_code,
                        "heading": response.heading.selected_code,
                        "subheading": response.subheading.selected_code
                    }
                )

                return response
        else:
            # No Langfuse tracking
            return await self._perform_classification(product_description, top_k)

    async def _perform_classification(self, product_description: str, top_k: int) -> ClassificationResponse:
        """Internal method to perform the actual classification."""
        import time
        start = time.time()

        # Chapter (2-digit)
        chapter_result = await self._classify_level(
            product_description,
            self.data_loader.codes_2digit,
            ClassificationLevel.CHAPTER,
            None,
            top_k
        )

        # Heading (4-digit) under selected chapter
        heading_codes = {
            code: hs for code, hs in self.data_loader.codes_4digit.items()
            if code.startswith(chapter_result.selected_code)
        }
        heading_result = await self._classify_level(
            product_description,
            heading_codes,
            ClassificationLevel.HEADING,
            chapter_result.selected_code,
            top_k
        )

        # Subheading (6-digit) under selected heading
        subheading_codes = {
            code: hs for code, hs in self.data_loader.codes_6digit.items()
            if code.startswith(heading_result.selected_code)
        }
        subheading_result = await self._classify_level(
            product_description,
            subheading_codes,
            ClassificationLevel.SUBHEADING,
            heading_result.selected_code,
            top_k
        )

        # Calculate overall confidence
        overall_confidence = (
            chapter_result.confidence * 0.3 +
            heading_result.confidence * 0.3 +
            subheading_result.confidence * 0.4
        )

        processing_time = (time.time() - start) * 1000

        return ClassificationResponse(
            product_description=product_description,
            final_code=subheading_result.selected_code,
            overall_confidence=overall_confidence,
            chapter=chapter_result,
            heading=heading_result,
            subheading=subheading_result,
            processing_time_ms=processing_time
        )

    async def _classify_level(
        self,
        product_description: str,
        codes_dict: Dict,
        level: ClassificationLevel,
        parent_code: Optional[str],
        top_k: int
    ) -> ClassificationResult:
        """Classify at a specific level (chapter/heading/subheading)."""
        # Step 1: Rank candidates
        ranked = await self._rank_candidates(
            product_description, codes_dict, level, parent_code, top_k
        )

        # Step 2: Select best candidate
        candidates_for_selection = [
            {"code": c.code, "description": c.description, "relevance_score": c.relevance_score}
            for c in ranked
        ]

        selection = await self._select_best(
            product_description, candidates_for_selection, level, parent_code
        )

        return ClassificationResult(
            level=level,
            selected_code=selection.selected_code,
            confidence=selection.confidence,
            reasoning=selection.reasoning
        )

    async def _rank_candidates(
        self,
        product_description: str,
        codes_dict: Dict,
        level: ClassificationLevel,
        parent_code: Optional[str],
        top_k: int
    ) -> List:
        """Rank all candidates at a level."""
        level_names = {"2": "CHAPTER", "4": "HEADING", "6": "SUBHEADING"}
        parent_info = f"Under parent: {parent_code}" if parent_code else "Root level"

        codes_list = "\n".join([
            f"{i+1}. {code}: {hs.description}"
            for i, (code, hs) in enumerate(codes_dict.items())
        ])

        system_prompt = """You are an HS code classification expert.
Rank the candidates by relevance to the product (0.0-1.0 score).
Consider specificity, accuracy, and trade classification principles."""

        user_prompt = f"""Product: "{product_description}"
Level: {level_names[level.value]} ({level.value}-digit)
{parent_info}

Codes to evaluate:
{codes_list}

Rank the top {top_k} most relevant codes."""

        try:
            result = await self.ranking_model.ainvoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ])

            # Filter valid codes
            valid_candidates = []
            for candidate in result.ranked_candidates:
                if candidate.code in codes_dict:
                    valid_candidates.append(candidate)

            return valid_candidates[:top_k]

        except Exception as e:
            print(f"Ranking failed: {e}, using fallback")
            # Fallback: return first top_k codes
            from hs_agent.models import RankedCandidate
            return [
                RankedCandidate(
                    code=code,
                    description=hs.description,
                    relevance_score=max(0.1, 0.8 - (i * 0.1)),
                    justification="Fallback ranking"
                )
                for i, (code, hs) in enumerate(list(codes_dict.items())[:top_k])
            ]

    async def _select_best(
        self,
        product_description: str,
        candidates: List[Dict],
        level: ClassificationLevel,
        parent_code: Optional[str]
    ) -> SelectionOutput:
        """Select the best candidate from ranked list."""
        level_names = {"2": "CHAPTER", "4": "HEADING", "6": "SUBHEADING"}
        parent_info = f"Under parent: {parent_code}" if parent_code else "Root level"

        candidates_text = "\n".join([
            f"• {c['code']}: {c['description']} (score: {c['relevance_score']:.2f})"
            for c in candidates
        ])

        system_prompt = """You are an HS code classification expert.
Select the BEST code from the ranked candidates.
Provide confidence score (0.0-1.0) and detailed reasoning."""

        user_prompt = f"""Product: "{product_description}"
Level: {level_names[level.value]} ({level.value}-digit)
{parent_info}

Ranked candidates:
{candidates_text}

Select the most accurate and specific code."""

        try:
            result = await self.selection_model.ainvoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ])
            return result

        except Exception as e:
            print(f"Selection failed: {e}, using fallback")
            # Fallback: select first candidate
            first = candidates[0]
            return SelectionOutput(
                selected_code=first["code"],
                confidence=0.5,
                reasoning=f"Fallback selection due to error: {e}"
            )