"""Main FastAPI application entry point for the Multi-Agent DevSecOps Incident Management System."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
import logging

from config import settings
from database.db import init_db
from simulator.infrastructure import SimulatedInfrastructure
from simulator.incident_generator import IncidentGenerator
from simulator.log_generator import LogGenerator
from simulator.metric_generator import MetricGenerator

from api.incidents import router as incidents_router
from api.agents import router as agents_router
from api.dashboard import router as dashboard_router
from api.knowledge import router as knowledge_router
from api.chat import router as chat_router
from api.websocket import ws_router, manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def metric_tick_loop(app):
    """Background task that updates simulator metrics and broadcasts to WebSocket clients."""
    while True:
        try:
            simulator = app.state.simulator
            simulator.tick()
            
            # Get current health data
            healths = simulator.get_all_health()
            health_data = []
            for h in healths:
                health_data.append({
                    "service_name": h.service_name,
                    "service_type": h.service_type,
                    "status": h.status.value,
                    "cpu_usage": round(h.cpu_usage, 1),
                    "memory_usage": round(h.memory_usage, 1),
                    "request_latency_ms": round(h.request_latency_ms, 1),
                    "error_rate": round(h.error_rate, 2),
                    "active_connections": h.active_connections,
                })

            await manager.broadcast("metrics", {
                "type": "METRIC_UPDATE",
                "data": health_data
            })
        except Exception as e:
            logger.error(f"Metric tick error: {e}")
        await asyncio.sleep(settings.SIMULATOR_TICK_INTERVAL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle."""
    logger.info("🚀 Starting Multi-Agent DevSecOps Incident Management System...")

    # Check API key
    if not settings.GOOGLE_API_KEY or settings.GOOGLE_API_KEY == "your_gemini_api_key_here":
        logger.warning("⚠️  GOOGLE_API_KEY is not set. AI agents will not function.")
        logger.warning("   Get a free key at: https://aistudio.google.com/apikey")
        logger.warning("   Set it in backend/.env file")
    else:
        logger.info("✅ Google Gemini API key configured")

    # Initialize database
    await init_db()
    logger.info("✅ Database initialized")

    # Initialize simulator
    simulator = SimulatedInfrastructure()
    log_generator = LogGenerator()
    metric_generator = MetricGenerator()
    incident_generator = IncidentGenerator(simulator)
    logger.info("✅ Simulated infrastructure initialized (6 services)")

    app.state.rag_retriever = None

    # Initialize RAG asynchronously in background
    async def init_rag_bg():
        try:
            from rag.vector_store import VectorStoreManager
            from rag.document_loader import DocumentLoader
            from rag.retriever import RAGRetriever

            vector_store = VectorStoreManager()
            doc_loader = DocumentLoader(vector_store)
            doc_loader.load_all()
            app.state.rag_retriever = RAGRetriever(vector_store)
            try:
                from tools.knowledge_tools import set_rag_retriever
                set_rag_retriever(app.state.rag_retriever)
            except Exception:
                pass
            logger.info("✅ RAG engine background initialization complete")
        except Exception as e:
            logger.warning(f"⚠️  RAG background init note: {e}")

    asyncio.create_task(init_rag_bg())

    # Store in app state
    app.state.simulator = simulator
    app.state.log_generator = log_generator
    app.state.metric_generator = metric_generator
    app.state.incident_generator = incident_generator
    app.state.war_room_sessions = {}
    app.state.active_incidents = {}

    # Wire up tools with simulator and RAG
    try:
        from tools.log_tools import set_simulator as set_log_sim
        from tools.metric_tools import set_simulator as set_metric_sim
        from tools.security_tools import set_simulator as set_security_sim
        from tools.infrastructure_tools import set_simulator as set_infra_sim
        from tools.knowledge_tools import set_rag_retriever

        set_log_sim(simulator)
        set_metric_sim(simulator)
        set_security_sim(simulator)
        set_infra_sim(simulator)
        if hasattr(app.state, 'rag_retriever') and app.state.rag_retriever:
            set_rag_retriever(app.state.rag_retriever)
        logger.info("✅ Agent tools wired to simulator and RAG")
    except Exception as e:
        logger.warning(f"⚠️  Tool wiring partially failed: {e}")

    # Start background metric loop
    tick_task = asyncio.create_task(metric_tick_loop(app))
    logger.info("✅ Background metric monitoring started")
    logger.info("="*60)
    logger.info("🎯 System ready! Dashboard: http://localhost:5173")
    logger.info("📡 API docs: http://localhost:8000/docs")
    logger.info("="*60)

    yield

    # Shutdown
    tick_task.cancel()
    logger.info("System shutdown complete.")


app = FastAPI(
    title="Multi-Agent DevSecOps Incident Management API",
    description="AI-powered incident management system with multiple specialized agents",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(incidents_router)
app.include_router(agents_router)
app.include_router(dashboard_router)
app.include_router(knowledge_router)
app.include_router(chat_router)
app.include_router(ws_router)


@app.get("/", tags=["root"])
async def root():
    """API root endpoint with system information."""
    return {
        "name": "Multi-Agent DevSecOps Incident Management API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "agents": 10,
        "description": "AI-powered incident management with collaborative multi-agent investigation",
    }


@app.get("/api/health", tags=["health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "simulator": "active",
        "database": "connected",
        "rag": "active" if hasattr(app.state, 'rag_retriever') and app.state.rag_retriever else "inactive",
    }
