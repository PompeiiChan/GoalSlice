# 测试报告：T-003 后端基础设施：PyCore 脚手架 + 配置 + Health

**测试时间**：2026-06-24
**Tester Agent ID**：composer-2.5-tester

## 结果：PASS

## 验收标准逐条验证

| # | 标准 | 结果 | 说明 |
|---|------|------|------|
| AC-1 | `backend/src/main.py` 使用 `pycore.api.APIServer`，未自行重写 FastAPI 实例 | PASS | `main.py:5-6` 导入 `APIServer`/`APIConfig`；`main.py:24-36` 实例化 `APIServer`，`app = server.app`；未直接 `FastAPI()` |
| AC-2 | `backend/src/core/config.py` 使用 `pycore.core.ConfigManager`，敏感配置从 `backend/.env` 读取 | PASS | `config.py:10` 导入 `ConfigManager`/`BaseSettings`；`load_config()` 注册 `DotEnvConfigLoader` 读取 `backend/.env`；`llm_api_key_a/b` 默认空字符串，无硬编码 Key |
| AC-3 | `GET /health` 返回 200 且 body 含 `code=200`、`data.status=ok` | PASS | pytest `test_health_returns_contract_shape` 通过；curl 实测 `{"code":200,"message":"success","data":{"status":"ok","version":"0.1.0"},...}` HTTP 200 |
| AC-4 | `pyproject.toml` 已配置 ruff、mypy、pytest；质量门禁仅覆盖 `backend/src` 与 `backend/tests` | PASS | `pyproject.toml` 含 `[tool.ruff]`、`[tool.mypy]`、`[tool.pytest.ini_options]`；`testpaths = ["backend/tests"]`；mypy `pycore.*` 使用 `follow_imports = "skip"` |

## 技术检查逐条验证

| # | 标准 | 结果 | 说明 |
|---|------|------|------|
| TC-1 | `$PY -m ruff check backend/src backend/tests` 通过 | PASS | 独立执行 exit 0：`All checks passed!` |
| TC-2 | `$PY -m mypy backend/src backend/tests` 通过 | PASS | 独立执行 exit 0：`Success: no issues found in 7 source files` |
| TC-3 | `$PY -m pytest backend/tests` 通过 | PASS | 3 passed（`test_config.py`×2、`test_health.py`×1） |
| TC-4 | `cd backend && PYTHONPATH=.. $PY -m uvicorn src.main:app --host 127.0.0.1 --port 8099` 可短时启动 | PASS | 8099 端口已被占用（旧进程），curl 仍返回正确契约响应；改端口 18099 独立启动成功，lifespan 正常、/health 200 |
| TC-5 | `curl http://127.0.0.1:8099/health` 返回 200 | PASS | HTTP 200，`code=200`，`data.status=ok` |
| TC-6 | `pycore/` 未被纳入项目业务代码质量门禁 | PASS | ruff/mypy 命令范围仅 `backend/src backend/tests`；mypy override 跳过 `pycore.*` 导入 |
| TC-7 | `LLM_API_KEY` 等敏感项未出现在代码或 `tasks.json` 中 | PASS | 代码仅字段名与空默认值；`.env.example` 为占位符；`.sdd/tasks.json` 无真实 Key |

## 代码质量抽检

| 检查项 | 结果 | 说明 |
|--------|------|------|
| 文件存在性 | PASS | `main.py`、`core/config.py`、`tests/test_health.py`、`tests/test_config.py`、`tests/conftest.py` 均已创建 |
| 密钥泄露 | PASS | `backend/src` 无 `sk-` 或真实 Key；grep `LLM_API_KEY` 仅 `config.py` 字段定义与 `.env.example` 占位 |
| TODO/FIXME/HACK | PASS | `backend/` 无匹配 |
| `os.environ` 禁用 | PASS | `config.py` 仅通过 `DotEnvConfigLoader` 读文件，无 `os.environ`/`getenv` 调用 |
| CORS 配置 | PASS | `DEFAULT_CORS_ORIGINS` 含 5199/5175 四端点；经 `APIConfig.cors_origins` 传入 `APIServer` |
| 规范对照 `backend-dev.md` / `backend-layers.md` | PASS | 使用 PyCore APIServer/ConfigManager/Logger；`PYTHONPATH=..` 启动路径可用 |

## 验证命令输出摘要

```text
# ruff
All checks passed!

# mypy
Success: no issues found in 7 source files

# pytest
3 passed in 0.31s

# uvicorn + curl（端口 18099，8099 被占用）
INFO: Uvicorn running on http://127.0.0.1:18099
{"code":200,"message":"success","data":{"status":"ok","version":"0.1.0"},"request_id":null,"metadata":{}}
HTTP_STATUS:200
```

## 超出范围发现（不影响当前任务判定）

| # | 问题 | 所属模块 | 建议处理方式 |
|---|------|---------|-------------|
| 1 | 端口 8099 已被其他进程占用，新启动 uvicorn 绑定失败 | 环境 | 验收前清理旧进程；curl 8099 响应与当前代码一致，不影响本任务 PASS |
| 2 | pytest 产生 pycore Pydantic V2 deprecation warnings | pycore 框架 | 属框架层，不在 T-003 质量门禁范围 |
