"""Simple FastAPI application for HS Agent."""

import time
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse

from hs_agent.agent import HSAgent
from hs_agent.data_loader import HSDataLoader
from hs_agent.models import (
    ClassificationRequest,
    ClassificationResponse,
    ClassificationResult,
    ClassificationLevel,
    MultiChoiceClassificationRequest,
    MultiChoiceClassificationResponse
)
from hs_agent.config.settings import settings
from hs_agent.utils.logger import get_logger

# Get centralized logger with consistent styling
logger = get_logger("hs_agent.api")


app = FastAPI(
    title="HS Agent",
    description="AI-powered HS code classification service",
    version="1.0.0"
)

# Mount static files
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Global instances
_data_loader = None
_agent_standard = None
_agent_wide_net = None
_agent_multi_choice = None


def get_agent(use_wide_net: bool = False):
    """Get or create agent instance."""
    global _data_loader, _agent_standard, _agent_wide_net, _agent_multi_choice

    # Initialize data loader if needed
    if _data_loader is None:
        logger.init_start("Data Loader")
        _data_loader = HSDataLoader()
        _data_loader.load_all_data()
        logger.init_complete("Data Loader", f"📊 Loaded {len(_data_loader.codes_6digit)} codes")

    # Get appropriate agent
    if use_wide_net:
        if _agent_wide_net is None:
            logger.init_start("Wide Net Agent", "high performance mode")
            _agent_wide_net = HSAgent(_data_loader, workflow_name="wide_net_classification")
            logger.init_complete("Wide Net Agent", "🎯 Chapter notes + path comparison")
        return _agent_wide_net
    else:
        if _agent_standard is None:
            logger.init_start("Standard Agent", "fast mode")
            _agent_standard = HSAgent(_data_loader, workflow_name="single_path_classification")
            logger.init_complete("Standard Agent", "⚡ One-shot hierarchical")
        return _agent_standard


# ========== HTML Pages ==========

@app.get("/classify")
async def classify_page():
    """Serve single classification UI."""
    return FileResponse(str(static_dir / "classify.html"))


@app.get("/classify-multi")
async def classify_multi_page():
    """Serve multi classification UI."""
    return FileResponse(str(static_dir / "classify-multi.html"))


# ========== API Endpoints ==========


@app.post("/api/classify", response_model=ClassificationResponse)
async def classify_product(request: ClassificationRequest):
    """Classify a product description to a single HS code (one-to-one).

    Returns the single best HS code path for the product.

    Two modes available:

    **Standard (fast)**: high_performance=False
    - One-shot hierarchical classification
    - Fast and efficient
    - Best for simple, unambiguous products

    **High Performance (accurate)**: high_performance=True
    - Wide net exploration: explores multiple paths at each level
    - Applies chapter notes with precedence rules and exclusions
    - Compares all paths to select the best
    - Slower but more accurate for complex/ambiguous products

    Parameters:
    - high_performance: Enable wide net approach with chapter notes (default: False)
    - max_selections: Only for high_performance mode - paths to explore (default: 3)
    """
    try:
        if request.high_performance:
            # High performance mode: use wide net approach
            agent = get_agent(use_wide_net=True)

            logger.info(f"🎯 [bold]High Performance Mode:[/bold] [cyan]{request.product_description}[/cyan] [dim](paths={request.max_selections})[/dim]")

            # Use multi classification with comparison
            multi_result = await agent.classify_multi(
                product_description=request.product_description,
                max_selections=request.max_selections
            )

            # Extract the final selected path for the response
            final_path = next((p for p in multi_result.paths if p.subheading_code == multi_result.final_selected_code), multi_result.paths[0])

            logger.classify_result(multi_result.final_selected_code, multi_result.final_confidence, f"✨ Explored {len(multi_result.paths)} paths")

            # Convert to ClassificationResponse format with additional info
            return ClassificationResponse(
                product_description=request.product_description,
                final_code=multi_result.final_selected_code,
                overall_confidence=multi_result.final_confidence,
                chapter=ClassificationResult(
                    level=ClassificationLevel.CHAPTER,
                    selected_code=final_path.chapter_code,
                    description=final_path.chapter_description,
                    confidence=multi_result.final_confidence,
                    reasoning=final_path.chapter_reasoning
                ),
                heading=ClassificationResult(
                    level=ClassificationLevel.HEADING,
                    selected_code=final_path.heading_code,
                    description=final_path.heading_description,
                    confidence=multi_result.final_confidence,
                    reasoning=final_path.heading_reasoning
                ),
                subheading=ClassificationResult(
                    level=ClassificationLevel.SUBHEADING,
                    selected_code=final_path.subheading_code,
                    description=final_path.subheading_description,
                    confidence=multi_result.final_confidence,
                    reasoning=final_path.subheading_reasoning
                ),
                processing_time_ms=multi_result.processing_time_ms,
                paths_explored=multi_result.paths,
                comparison_reasoning=multi_result.final_reasoning,
                comparison_summary=multi_result.comparison_summary
            )
        else:
            # Standard mode: one-shot classification
            agent = get_agent(use_wide_net=False)

            logger.classify_start(request.product_description, {"mode": "standard"})
            result = await agent.classify(
                product_description=request.product_description
            )

            logger.classify_result(result.final_code, result.overall_confidence)
            return result

    except Exception as e:
        logger.error_msg("Classification", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/classify/multi", response_model=MultiChoiceClassificationResponse)
async def classify_product_multi(request: MultiChoiceClassificationRequest):
    """Explore multiple classification paths for ambiguous products.

    Returns 1-N possible HS code paths showing different classification interpretations.

    Parameters:
    - max_selections: Number of codes to select at each level (default: 3)

    Example with max_selections=3:
    - Evaluates all chapters, selects best 1-3
    - For each chapter, evaluates headings, selects best 1-3
    - For each heading, evaluates subheadings, selects best 1-3
    - Explores up to 27 possible paths
    """
    try:
        # Use multi-choice classification workflow (not wide net)
        global _agent_multi_choice, _data_loader
        
        # Initialize data loader if needed
        if _data_loader is None:
            logger.init_start("Data Loader")
            _data_loader = HSDataLoader()
            _data_loader.load_all_data()
            logger.init_complete("Data Loader", f"📊 Loaded {len(_data_loader.codes_6digit)} codes")
        
        # Initialize multi-choice agent if needed
        if _agent_multi_choice is None:
            logger.init_start("Multi-Choice Agent", "1-to-N paths")
            _agent_multi_choice = HSAgent(_data_loader, workflow_name="multi_choice_classification")
            logger.init_complete("Multi-Choice Agent", "🔀 Adaptive path exploration")
        
        agent = _agent_multi_choice

        logger.info(f"🔀 [bold]Multi-Choice Classification:[/bold] [cyan]{request.product_description}[/cyan] [dim](max_selections={request.max_selections})[/dim]")
        result = await agent.classify_multi(
            product_description=request.product_description,
            max_selections=request.max_selections
        )

        logger.info(f"✨ Multi-Choice Result: Explored {len(result.paths)} path(s) → Final: {result.final_selected_code} (confidence: {result.final_confidence:.2%})")
        return result

    except Exception as e:
        logger.error_msg("Multi-Choice Classification", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        agent = get_agent()
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "model": settings.default_model_name,
            "codes_loaded": {
                "chapters": len(agent.data_loader.codes_2digit),
                "headings": len(agent.data_loader.codes_4digit),
                "subheadings": len(agent.data_loader.codes_6digit)
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


@app.get("/")
async def root():
    """Root endpoint - redirect to classification UI."""
    return RedirectResponse(url="/classify")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.api_port)