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
    MultiChoiceClassificationRequest,
    MultiChoiceClassificationResponse
)
from hs_agent.config.settings import settings


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
_agent = None


def get_agent():
    """Get or create agent instance."""
    global _data_loader, _agent

    if _agent is None:
        print("Initializing HS Agent...")
        _data_loader = HSDataLoader()
        _data_loader.load_all_data()
        _agent = HSAgent(_data_loader)
        print("HS Agent ready")

    return _agent


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

    Parameters:
    - top_k: Number of top candidates to consider during ranking (performance optimization).
             Higher values = more thorough but slower. Default: 10

    Example: top_k=10 means:
    - Rank all chapters → select the single best from top 10
    - Rank headings under that chapter → select the single best from top 10
    - Rank subheadings under that heading → select the single best from top 10
    - Returns 1 final HS code
    """
    try:
        agent = get_agent()

        print(f"Classifying: {request.product_description} (top_k={request.top_k})")
        result = await agent.classify(
            product_description=request.product_description,
            top_k=request.top_k
        )

        print(f"Result: {result.final_code} (confidence: {result.overall_confidence:.2f})")
        return result

    except Exception as e:
        print(f"Classification failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/classify/multi", response_model=MultiChoiceClassificationResponse)
async def classify_product_multi(request: MultiChoiceClassificationRequest):
    """Classify a product and return 1-N possible HS code paths.

    Use this for ambiguous products that could fit into multiple HS codes.

    Parameters:
    - top_k: How many candidates to RANK at each level (e.g., rank top 10 from all chapters)
    - max_selections: How many to SELECT from ranked candidates (e.g., pick best 1-3 from top 10)

    Example: top_k=10, max_selections=3 means:
    - Rank all chapters → get top 10 → select best 1-3
    - For each selected chapter, rank headings → get top 10 → select best 1-3
    - For each selected heading, rank subheadings → get top 10 → select best 1-3
    - Returns up to 27 possible paths (limited by MAX_OUTPUT_PATHS setting)
    """
    try:
        agent = get_agent()

        print(f"Multi-classifying: {request.product_description} (top_k={request.top_k}, max_selections={request.max_selections})")
        result = await agent.classify_multi(
            product_description=request.product_description,
            top_k=request.top_k,
            max_selections=request.max_selections
        )

        print(f"Result: {len(result.paths)} path(s)")
        return result

    except Exception as e:
        print(f"Multi-classification failed: {e}")
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