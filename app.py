"""FastAPI application for HS Agent - Tax Code Mapping and Classification Service."""

import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, HTTPException, File, UploadFile, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel

from hs_agent.workflows.tax_code_mapper import TaxCodeMapper
from hs_agent.config import settings, AgentType
from hs_agent.core.data_loader import HSDataLoader
from hs_agent.agents.langgraph.agents import HSLangGraphAgent
from hs_agent.agents.traditional.agents import HSClassificationAgent
from hs_agent.core.models.requests import ClassificationRequest
from hs_agent.core.models.responses import ClassificationResponse
from hs_agent.core.logging import get_logger
from hs_agent.core.exceptions import HSAgentError

logger = get_logger(__name__)


# FastAPI app initialization
app = FastAPI(
    title="HS Agent - Classification and Mapping Service",
    description="AI-powered Harmonized System code classification and tax code mapping service",
    version="1.0.0"
)

# Data models
class MappingRequest(BaseModel):
    avalara_code: str
    description: str
    additional_info: Optional[str] = None

class MappingResponse(BaseModel):
    avalara_code: str
    combined_description: str
    hs_code: str
    hs_description: str
    confidence: float
    reasoning: str
    processing_time_ms: float
    hierarchical_classification: Dict[str, Any]

class BatchMappingRequest(BaseModel):
    count: int = 10
    confidence_threshold: float = 0.6

class AnalysisStats(BaseModel):
    total_processed: int
    successful_mappings: int
    failed_mappings: int
    average_confidence: float
    high_confidence_count: int
    most_common_hs_codes: List[Dict[str, Any]]

# Global variables for caching
cached_results_data = None
cached_stats = None
mapper_instance = None
data_loader_instance = None
langgraph_agent_instance = None
traditional_agent_instance = None

# Setup static files directory
static_dir = Path("static")
static_dir.mkdir(exist_ok=True)

# Copy HTML and JSON files to static directory
def setup_static_files():
    """Copy analysis files to static directory."""
    html_file = "tax_to_hs_mapping_analysis.html"
    json_file = "tax_to_hs_mapping_100_enhanced_20250922_171755.json"

    if os.path.exists(html_file):
        import shutil
        shutil.copy(html_file, static_dir / "index.html")

    if os.path.exists(json_file):
        import shutil
        shutil.copy(json_file, static_dir / "mapping_data.json")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

def get_data_loader():
    """Get or create data loader instance."""
    global data_loader_instance
    if data_loader_instance is None:
        data_loader_instance = HSDataLoader()
        data_loader_instance.load_all_data()
        logger.info("📊 Data loader initialized and loaded")
    return data_loader_instance


def get_agent(agent_type: AgentType):
    """Get or create agent instance based on type."""
    global langgraph_agent_instance, traditional_agent_instance
    
    data_loader = get_data_loader()
    
    if agent_type == AgentType.LANGGRAPH:
        if langgraph_agent_instance is None:
            langgraph_agent_instance = HSLangGraphAgent(data_loader)
            logger.info("🤖 LangGraph agent initialized")
        return langgraph_agent_instance
    elif agent_type == AgentType.TRADITIONAL:
        if traditional_agent_instance is None:
            traditional_agent_instance = HSClassificationAgent(data_loader)
            logger.info("🤖 Traditional agent initialized")
        return traditional_agent_instance
    else:
        raise ValueError(f"Unknown agent type: {agent_type}")


def get_mapper():
    """Get or create mapper instance."""
    global mapper_instance
    if mapper_instance is None:
        mapper_instance = TaxCodeMapper("data/avalara_tax_codes.xlsx", confidence_threshold=0.6)
    return mapper_instance

def load_results_data():
    """Load and cache results data."""
    global cached_results_data, cached_stats

    if cached_results_data is None:
        json_file = "tax_to_hs_mapping_100_enhanced_20250922_171755.json"
        if os.path.exists(json_file):
            with open(json_file, 'r', encoding='utf-8') as f:
                cached_results_data = json.load(f)

            # Calculate stats
            mappings = cached_results_data['mappings']
            confidences = [m['hs_classification']['overall_confidence'] for m in mappings]

            # Count HS codes
            hs_code_counts = {}
            for mapping in mappings:
                code = mapping['hs_classification']['final_hs_code']
                hs_code_counts[code] = hs_code_counts.get(code, 0) + 1

            most_common = sorted(hs_code_counts.items(), key=lambda x: x[1], reverse=True)[:10]

            cached_stats = AnalysisStats(
                total_processed=len(mappings),
                successful_mappings=len([m for m in mappings if not m.get('error')]),
                failed_mappings=len([m for m in mappings if m.get('error')]),
                average_confidence=sum(confidences) / len(confidences),
                high_confidence_count=len([c for c in confidences if c >= 0.8]),
                most_common_hs_codes=[{"hs_code": code, "count": count} for code, count in most_common]
            )

    return cached_results_data, cached_stats

# === Classification Endpoints ===

@app.post("/api/classify", response_model=ClassificationResponse)
async def classify_product(request: ClassificationRequest):
    """Classify a product description into an HS code.
    
    This endpoint performs hierarchical HS code classification using AI agents
    to determine the most appropriate 6-digit Harmonized System code.
    """
    try:
        # Use configured defaults if not specified
        agent_type = request.agent_type or settings.default_agent_type
        top_k = request.top_k or settings.default_top_k
        
        logger.info(
            "🎯 Starting classification request",
            product_description=request.product_description,
            agent_type=agent_type.value,
            top_k=top_k
        )
        
        # Get the appropriate agent
        agent = get_agent(agent_type)
        
        # Perform classification
        start_time = time.time()
        result = await agent.classify_hierarchical(
            product_description=request.product_description,
            top_k=top_k
        )
        processing_time_ms = (time.time() - start_time) * 1000
        
        # Get HS code description from data loader
        data_loader = get_data_loader()
        final_hs_code = result["final_code"]
        hs_code_info = data_loader.get_code_info(final_hs_code)
        final_description = hs_code_info.description if hs_code_info else "Description not available"
        
        # Build response
        response = ClassificationResponse(
            product_description=request.product_description,
            final_hs_code=final_hs_code,
            final_description=final_description,
            overall_confidence=result["overall_confidence"],
            processing_time_ms=processing_time_ms,
            agent_type=agent_type.value,
            timestamp=datetime.now()
        )
        
        # Add detailed results if requested
        if request.include_reasoning:
            response.chapter_result = result.get("chapter")
            response.heading_result = result.get("heading")
            response.subheading_result = result.get("subheading")
            response.reasoning = f"Classification completed using {agent_type.value} agent with {result['overall_confidence']:.2%} confidence."
        
        logger.info(
            "✅ Classification completed",
            final_code=final_hs_code,
            confidence=result["overall_confidence"],
            processing_time_ms=processing_time_ms
        )
        
        return response
        
    except HSAgentError as e:
        logger.error(f"Classification failed: {e.message}", error_details=e.details)
        raise HTTPException(status_code=400, detail=f"Classification failed: {e.message}")
    except Exception as e:
        logger.error(f"Unexpected error during classification: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/api/info")
async def get_server_info():
    """Get server information and configuration."""
    try:
        data_loader = get_data_loader()
        stats = data_loader.data_statistics
        
        return {
            "service": "HS Agent Classification and Mapping Service",
            "version": "1.0.0",
            "timestamp": datetime.now().isoformat(),
            "configuration": {
                "default_agent_type": settings.default_agent_type.value,
                "default_model": settings.default_model_name,
                "default_top_k": settings.default_top_k,
                "api_host": settings.api_host,
                "api_port": settings.api_port
            },
            "data_statistics": stats,
            "available_agents": [agent.value for agent in AgentType],
            "endpoints": {
                "classification": "/api/classify",
                "health": "/health",
                "info": "/api/info",
                "docs": "/docs"
            }
        }
    except Exception as e:
        logger.error(f"Error getting server info: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting server info: {str(e)}")


# === Tax Code Mapping Endpoints ===

# API Routes

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main dashboard."""
    return FileResponse("static/index.html")

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    """Serve the analysis dashboard."""
    setup_static_files()
    return FileResponse("static/index.html")

@app.get("/api/stats", response_model=AnalysisStats)
async def get_stats():
    """Get analysis statistics."""
    _, stats = load_results_data()
    if stats is None:
        raise HTTPException(status_code=404, detail="No analysis data found")
    return stats

@app.get("/api/mappings")
async def get_mappings(
    limit: Optional[int] = None,
    confidence_min: Optional[float] = None,
    confidence_max: Optional[float] = None,
    hs_code: Optional[str] = None,
    search: Optional[str] = None
):
    """Get mapping results with optional filtering."""
    data, _ = load_results_data()
    if data is None:
        raise HTTPException(status_code=404, detail="No mapping data found")

    mappings = data['mappings']

    # Apply filters
    if confidence_min is not None:
        mappings = [m for m in mappings if m['hs_classification']['overall_confidence'] >= confidence_min]

    if confidence_max is not None:
        mappings = [m for m in mappings if m['hs_classification']['overall_confidence'] <= confidence_max]

    if hs_code:
        mappings = [m for m in mappings if m['hs_classification']['final_hs_code'] == hs_code]

    if search:
        search_lower = search.lower()
        mappings = [m for m in mappings if (
            search_lower in m['avalara_code'].lower() or
            search_lower in m.get('combined_description', '').lower() or
            search_lower in m['hs_classification']['final_hs_code'].lower() or
            search_lower in m['hs_classification']['final_hs_description'].lower()
        )]

    if limit:
        mappings = mappings[:limit]

    return {
        "count": len(mappings),
        "mappings": mappings
    }

@app.get("/api/mapping/{avalara_code}")
async def get_mapping_by_code(avalara_code: str):
    """Get detailed mapping for a specific Avalara code."""
    data, _ = load_results_data()
    if data is None:
        raise HTTPException(status_code=404, detail="No mapping data found")

    mapping = next((m for m in data['mappings'] if m['avalara_code'] == avalara_code), None)
    if mapping is None:
        raise HTTPException(status_code=404, detail=f"Mapping for code {avalara_code} not found")

    return mapping

@app.post("/api/map", response_model=MappingResponse)
async def map_single_code(request: MappingRequest):
    """Map a single tax code to HS code."""
    try:
        mapper = get_mapper()

        # Create tax code entry
        from hs_agent.workflows.tax_code_mapper import TaxCodeEntry
        tax_entry = TaxCodeEntry(
            avalara_code=request.avalara_code,
            description=request.description,
            additional_info=request.additional_info or ""
        )

        # Perform mapping
        result = await mapper.map_single_tax_code_enhanced(tax_entry)

        return MappingResponse(
            avalara_code=result.avalara_code,
            combined_description=result.avalara_description + (f". {result.avalara_additional_info}" if result.avalara_additional_info else ""),
            hs_code=result.hs_code,
            hs_description=result.hs_description,
            confidence=result.confidence,
            reasoning=result.reasoning,
            processing_time_ms=result.processing_time_ms,
            hierarchical_classification=result.full_classification
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Mapping failed: {str(e)}")

@app.post("/api/batch-map")
async def start_batch_mapping(request: BatchMappingRequest, background_tasks: BackgroundTasks):
    """Start batch mapping process."""

    async def run_batch_mapping(count: int, threshold: float):
        """Background task to run batch mapping."""
        try:
            mapper = EnhancedTaxCodeMapper("data/avalara_tax_codes.xlsx", confidence_threshold=threshold)
            codes_to_process = mapper.tax_codes[:count]

            results = []
            for tax_entry in codes_to_process:
                result = await mapper.map_single_tax_code_enhanced(tax_entry)
                results.append(result)

            # Save results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_data = {
                "metadata": {
                    "total_processed": len(results),
                    "successful_mappings": len([r for r in results if not r.error]),
                    "failed_mappings": len([r for r in results if r.error]),
                    "confidence_threshold": threshold,
                    "processing_timestamp": datetime.now().isoformat(),
                    "description": f"Batch mapping of {count} tax codes"
                },
                "mappings": [result.to_dict() for result in results]
            }

            output_file = f"batch_mapping_{count}_{timestamp}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)

            print(f"Batch mapping completed: {output_file}")

        except Exception as e:
            print(f"Batch mapping failed: {e}")

    background_tasks.add_task(run_batch_mapping, request.count, request.confidence_threshold)

    return {
        "message": f"Batch mapping started for {request.count} codes",
        "status": "processing",
        "estimated_time_minutes": request.count * 0.75  # Rough estimate
    }

@app.get("/api/hs-codes")
async def get_unique_hs_codes():
    """Get list of unique HS codes from results."""
    data, _ = load_results_data()
    if data is None:
        raise HTTPException(status_code=404, detail="No mapping data found")

    hs_codes = list(set(m['hs_classification']['final_hs_code'] for m in data['mappings']))
    hs_codes.sort()

    return {"hs_codes": hs_codes}

@app.get("/health")
async def health_check():
    """Comprehensive health check endpoint."""
    try:
        health_status = "healthy"
        checks = {}
        
        # Check data loader
        try:
            data_loader = get_data_loader()
            stats = data_loader.data_statistics
            checks["data_loader"] = {
                "status": "healthy",
                "codes_loaded": stats["subheadings"],
                "details": stats
            }
        except Exception as e:
            checks["data_loader"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_status = "degraded"
        
        # Check agents
        for agent_type in AgentType:
            try:
                agent = get_agent(agent_type)
                checks[f"agent_{agent_type.value}"] = {
                    "status": "healthy",
                    "type": agent_type.value
                }
            except Exception as e:
                checks[f"agent_{agent_type.value}"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
                health_status = "degraded"
        
        # Check Google API configuration
        if settings.google_api_enabled:
            checks["google_api"] = {
                "status": "configured",
                "model": settings.default_model_name
            }
        else:
            checks["google_api"] = {
                "status": "not_configured",
                "warning": "Google API key not set"
            }
            if health_status == "healthy":
                health_status = "degraded"
        
        return {
            "status": health_status,
            "timestamp": datetime.now().isoformat(),
            "service": "HS Agent Classification and Mapping Service",
            "version": "1.0.0",
            "checks": checks
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "service": "HS Agent Classification and Mapping Service",
            "error": str(e)
        }

# Setup static files on startup
@app.on_event("startup")
async def startup_event():
    """Setup static files on startup."""
    setup_static_files()
    print("🚀 Tax Code Mapping Service started")
    print(f"📊 Dashboard available at: http://{settings.api_host}:{settings.api_port}/dashboard")
    print(f"📚 API docs available at: http://{settings.api_host}:{settings.api_port}/docs")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.api_host, port=settings.api_port)
