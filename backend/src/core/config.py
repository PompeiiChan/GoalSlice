"""应用配置：基于 PyCore ConfigManager，从 backend/.env 文件读取（不读进程环境变量）。"""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from pydantic import Field

from pycore.core.config import BaseSettings, ConfigLoader, ConfigManager

_BACKEND_DIR = Path(__file__).resolve().parents[2]
_DEFAULT_ENV_PATH = _BACKEND_DIR / ".env"

_config_manager: ConfigManager[AppSettings] | None = None

DEFAULT_CORS_ORIGINS = [
    "http://localhost:5199",
    "http://127.0.0.1:5199",
    "http://localhost:5175",
    "http://127.0.0.1:5175",
]


class DotEnvConfigLoader(ConfigLoader):
    """解析 KEY=VALUE 格式的 .env 文件（仅读文件，不使用 os.environ）。"""

    def supports(self, path: Path) -> bool:
        return path.name == ".env" or path.suffix.lower() == ".env"

    def load(self, path: Path) -> dict[str, Any]:
        if not path.is_file():
            return {}

        parsed: dict[str, Any] = {}
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip().lower()
            value = value.strip().strip('"').strip("'")
            parsed[key] = _coerce_value(value)
        return parsed


def _coerce_value(value: str) -> Any:
    lower = value.lower()
    if lower in {"true", "false"}:
        return lower == "true"
    if value.isdigit():
        return int(value)
    return value


class AppSettings(BaseSettings):
    debug: bool = False
    app_host: str = "127.0.0.1"
    app_port: int = 8099
    database_url: str = "sqlite+aiosqlite:///./data/goalslice.db"
    llm_base_url: str = "https://api.siliconflow.cn/v1"
    llm_model: str = "Qwen/Qwen3.5-27B"
    llm_api_key_a: str = ""
    llm_api_key_b: str = ""
    cors_origins: list[str] = Field(default_factory=lambda: list(DEFAULT_CORS_ORIGINS))


def load_config(env_path: Path | str | None = None) -> ConfigManager[AppSettings]:
    """加载 backend/.env 到 ConfigManager 单例。"""
    global _config_manager

    ConfigManager.reset()
    manager = ConfigManager[AppSettings]()
    manager.register_loader(DotEnvConfigLoader())

    path = Path(env_path) if env_path else _DEFAULT_ENV_PATH
    file_data = DotEnvConfigLoader().load(path) if path.is_file() else {}

    settings_data = {**file_data}
    if "cors_origins" not in settings_data:
        settings_data["cors_origins"] = list(DEFAULT_CORS_ORIGINS)

    manager.load_from_dict(AppSettings, settings_data)
    _config_manager = manager
    return manager


def get_settings() -> AppSettings:
    if _config_manager is None or _config_manager.settings is None:
        load_config()
    assert _config_manager is not None
    return cast(AppSettings, _config_manager.settings)
