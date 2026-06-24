from pathlib import Path

from src.core.config import AppSettings, DotEnvConfigLoader, load_config

from pycore.core.config import ConfigManager


def test_dotenv_loader_reads_file_without_os_environ(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "APP_HOST=127.0.0.1\nAPP_PORT=8099\nDEBUG=true\n",
        encoding="utf-8",
    )

    data = DotEnvConfigLoader().load(env_file)
    assert data["app_host"] == "127.0.0.1"
    assert data["app_port"] == 8099
    assert data["debug"] is True


def test_load_config_uses_config_manager(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("APP_PORT=8765\n", encoding="utf-8")

    ConfigManager.reset()
    manager = load_config(env_file)
    settings = manager.settings

    assert isinstance(settings, AppSettings)
    assert settings.app_port == 8765
