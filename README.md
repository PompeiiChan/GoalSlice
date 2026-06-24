# GoalSlice 就这

把长期职业目标拆成 **7 天可完成的小事件**，每天一件事，低压力推进成长。

## 功能概览

- **目标输入与澄清**（P01/P02）：描述目标，回答 5 道澄清题
- **计划生成与接受**（P03）：AI 生成 7 日主线，用户确认后开始
- **每日任务与反馈**（P04/P05）：完成任务后获得意义解释与成长资产
- **任务降级**（P06）：任务太难时可选择更小的替代方案
- **进行中枢**（P08）：查看本周进度、资产与主线详情
- **周复盘**（P07）：7 天完成后复盘，可开启下一周或暂停

## 技术栈

| 层 | 技术 |
|----|------|
| 前端 | React 18 + TypeScript + Vite + Ant Design |
| 后端 | FastAPI + SQLAlchemy + SQLite |
| AI | 硅基流动（OpenAI 兼容 API），模型 `Qwen/Qwen3.5-27B` |

## 快速开始

详细步骤见 **[docs/startup.md](docs/startup.md)**。

```bash
# 1. 后端
cp backend/.env.example backend/.env   # 填入 LLM_API_KEY_A/B
cd backend
PYTHONPATH=.. ../.venv/bin/uvicorn src.main:app --host 127.0.0.1 --port 8099 --reload

# 2. 前端
cd frontend
npm install
npm run dev   # http://127.0.0.1:5199
```

真实 API 联调时，将 `frontend/.env` 或 `.env.local` 中 `VITE_USE_MOCK` 设为 `false`。

## 目录结构

```
goalslice/
├── backend/     # FastAPI 后端与 API
├── frontend/    # React 前端
├── pycore/      # 内部 Python 框架
├── docs/        # PRD、API 契约、原型、启动指南
└── pyproject.toml
```

## 测试

```bash
# 后端（72 项）
cd backend && PYTHONPATH=.. ../.venv/bin/python -m pytest tests/ -q

# E2E API 回归
PYTHONPATH=.. ../.venv/bin/python -m pytest tests/test_e2e.py -v

# 前端
cd frontend && npm run type-check && npm run lint && npm run build
```

## 文档

- [启动指南](docs/startup.md)
- [产品需求](docs/PRD.md)
- [API 契约](docs/api-contracts.md)
- [开发计划](docs/Plan.md)

## License

Private — 仅供项目所有者使用。
