import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from backend.app.core.config import settings
from backend.app.core.database import Base, engine
from backend.app.websocket.manager import ws_manager
from backend.app.monitoring.linux_collector import LinuxCollector

from backend.app.api.v1.endpoints import (
    system,
    discovery,
    security,
    performance,
    ai,
    actions,
    reports,
    agents,
    servers,
)
from backend.app.workers.remote_monitor import remote_monitoring_loop

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("infrapilot-ai")

# Create database tables
Base.metadata.create_all(bind=engine)

# Backward-compatible migrations
with engine.connect() as conn:
    for migration_sql in [
        "ALTER TABLE approved_actions ADD COLUMN expires_at DATETIME;",
        "ALTER TABLE approved_actions ADD COLUMN server_id VARCHAR(64) DEFAULT 'local';",
        "ALTER TABLE system_snapshots ADD COLUMN server_id VARCHAR(64) DEFAULT 'local';",
        "ALTER TABLE process_snapshots ADD COLUMN server_id VARCHAR(64) DEFAULT 'local';",
        "ALTER TABLE service_snapshots ADD COLUMN server_id VARCHAR(64) DEFAULT 'local';",
        "ALTER TABLE container_snapshots ADD COLUMN server_id VARCHAR(64) DEFAULT 'local';",
        "ALTER TABLE security_findings ADD COLUMN server_id VARCHAR(64) DEFAULT 'local';",
    ]:
        try:
            conn.execute(text(migration_sql))
            conn.commit()
        except Exception:
            pass


async def metrics_broadcaster():
    """Background task to broadcast real host metrics to connected WebSocket clients."""
    while True:
        try:
            if ws_manager.active_connections:
                metrics = LinuxCollector.collect_full_metrics()
                await ws_manager.broadcast({
                    "type": "metrics_update",
                    "data": metrics,
                })
        except Exception as e:
            logger.error(f"Error in metrics broadcaster: {e}")
        await asyncio.sleep(settings.METRIC_COLLECTION_INTERVAL_SECONDS)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: start background metrics broadcast and remote monitor tasks
    metrics_task = asyncio.create_task(metrics_broadcaster())
    monitor_task = asyncio.create_task(remote_monitoring_loop())
    yield
    # Shutdown: cancel tasks
    metrics_task.cancel()
    monitor_task.cancel()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="InfraPilot AI — AI-Powered Infrastructure Monitoring, Security Auditing, Remote Server Management & DevOps Automation Platform.",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include REST Routers
api_v1 = settings.API_PREFIX
app.include_router(system.router, prefix=api_v1, tags=["System"])
app.include_router(discovery.router, prefix=api_v1, tags=["Discovery"])
app.include_router(security.router, prefix=api_v1, tags=["Security"])
app.include_router(performance.router, prefix=api_v1, tags=["Performance"])
app.include_router(ai.router, prefix=api_v1, tags=["AI Assistant"])
app.include_router(actions.router, prefix=api_v1, tags=["Actions"])
app.include_router(reports.router, prefix=api_v1, tags=["Reports"])
app.include_router(agents.router, prefix=api_v1, tags=["Registered Agents"])
app.include_router(servers.router, prefix=api_v1 + "/servers", tags=["Managed Servers"])


@app.websocket("/ws/metrics")
async def websocket_metrics_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        initial_metrics = LinuxCollector.collect_full_metrics()
        await websocket.send_json({"type": "metrics_update", "data": initial_metrics})
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception:
        ws_manager.disconnect(websocket)


@app.get("/")
def root():
    return {
        "app": settings.APP_NAME,
        "tagline": settings.APP_TAGLINE,
        "version": settings.APP_VERSION,
        "docs_url": "/docs",
        "api_prefix": settings.API_PREFIX,
    }
