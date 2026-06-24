"""GoalSlice 后端入口 — PyCore APIServer。"""

from __future__ import annotations

from pycore.api import APIConfig, APIServer
from pycore.api.responses import APIResponse, success_response
from pycore.core import Logger, LoggerConfig, LogLevel, get_logger
from src.api.routes import router as api_router
from src.core.config import get_settings, load_config
from src.db.session import close_db, init_db

APP_VERSION = "0.1.0"

load_config()
settings = get_settings()

Logger.configure(
    LoggerConfig(
        level=LogLevel.DEBUG if settings.debug else LogLevel.INFO,
        app_name="goalslice",
        json_format=False,
    )
)
logger = get_logger()

server = APIServer(
    APIConfig(
        title="GoalSlice 就这 API",
        description="GoalSlice MVP backend",
        version=APP_VERSION,
        host=settings.app_host,
        port=settings.app_port,
        debug=settings.debug,
        cors_origins=settings.cors_origins,
    )
)
server.on_startup(init_db)
server.on_shutdown(close_db)

app = server.app
app.include_router(api_router)

# APIServer 内置 /health 返回 status=healthy；替换为 api-contracts 约定
app.router.routes = [
    route for route in app.router.routes if getattr(route, "path", None) != "/health"
]


@app.get("/health", tags=["system"])
async def health_check() -> APIResponse:
    return success_response({"status": "ok", "version": APP_VERSION})


logger.info("GoalSlice API configured", host=settings.app_host, port=settings.app_port)
