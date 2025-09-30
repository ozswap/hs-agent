"""Simple FastAPI application for HS Agent."""

import time
from datetime import datetime
from fastapi import FastAPI, HTTPException

from hs_agent.agent import HSAgent
from hs_agent.data_loader import HSDataLoader
from hs_agent.models import ClassificationRequest, ClassificationResponse
from hs_agent.config.settings import settings


app = FastAPI(
    title="HS Agent",
    description="AI-powered HS code classification service",
    version="1.0.0"
)

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


@app.post("/api/classify", response_model=ClassificationResponse)
async def classify_product(request: ClassificationRequest):
    """Classify a product description to get HS code."""
    try:
        agent = get_agent()

        print(f"Classifying: {request.product_description}")
        result = await agent.classify(
            product_description=request.product_description,
            top_k=request.top_k
        )

        print(f"Result: {result.final_code} (confidence: {result.overall_confidence:.2f})")
        return result

    except Exception as e:
        print(f"Classification failed: {e}")
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
    """Root endpoint."""
    return {
        "service": "HS Agent",
        "version": "1.0.0",
        "endpoints": {
            "classify": "/api/classify",
            "health": "/health",
            "docs": "/docs"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.api_port)