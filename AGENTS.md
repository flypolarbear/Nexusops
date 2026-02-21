# AI Agent Guidelines for NexusOps

Welcome to NexusOps! This is an AI Native Operations Platform focused on the "Vibe Coding" workflow (Rapid Dev -> Rapid Iterate -> Rapid Deploy) and a multi-agent ecosystem. This file provides critical context, commands, and rules for AI agents operating in this repository.

## 🏗️ Architecture & Stack
*   **Frontend**: React 18, TypeScript, Vite, Ant Design, TailwindCSS, Zustand (State Management). Located in `/frontend`.
*   **Backend**: Python 3.10+, FastAPI, async SQLAlchemy (PostgreSQL), Pydantic v2. Located in `/backend/app`.
    *   *Note*: The backend was recently migrated from Go to Python. Ignore legacy `.go` files if encountered; the source of truth is `backend/app/*.py`.
*   **Infrastructure**: Docker Compose (`docker-compose.middleware.yml`).

## 🚀 Build, Lint, and Test Commands

### Backend (Python)
Always run commands with the `workdir` set to `/Users/hendrix/AgentSpace/NexusOps/backend`.
*   **Run Server**: `uvicorn app.main:app --reload --port 8000`
*   **Format & Lint**: `ruff check . --fix` and `black .` (Install these tools via pip if missing).
*   **Type Check**: `mypy app/`
*   **Test All**: `pytest tests/ -v`
*   **Test Single File**: `pytest tests/path_to_test.py -v`
*   **Test Specific Class/Func**: `pytest tests/path_to_test.py::TestClass::test_method -v`

### Frontend (TypeScript/React)
Always run commands with the `workdir` set to `/Users/hendrix/AgentSpace/NexusOps/frontend`.
*   **Install Deps**: `npm install`
*   **Run Dev Server**: `npm run dev` (Runs on port 3000, proxies `/api` to `localhost:8000`).
*   **Build**: `npm run build`
*   **Lint**: `npm run lint`
*   **End-to-End Tests**: Use the native Playwright python scripts with the `webapp-testing` skill for E2E validation (e.g. `python scripts/with_server.py ...`).

## ✍️ Code Style & Conventions

### 1. General Rules
*   **File Paths**: Always use absolute paths when reading or writing files via tools.
*   **No Speculative Deletions**: Do not remove existing logic (especially related to `VIBE_CODING_WORKFLOW` or `Agent Market`) unless explicitly instructed or if it directly conflicts with new MVP specs.
*   **Agent Driven Design**: Ensure components support Agent interaction (e.g., JSON schemas for inputs/outputs, structured responses via `AgentResponseRenderer`).

### 2. Backend (FastAPI / Python)
*   **Async First**: Use `async def` for API endpoints and `AsyncSession` for SQLAlchemy database operations.
*   **Pydantic**: Use Pydantic v2 schemas (`BaseModel`) for request/response validation. Segregate them in `app/models/schemas.py`.
*   **Dependency Injection**: Use `Depends(get_db)` for database sessions.
*   **Routing**: Organize endpoints logically by feature in `app/api/` (e.g., `agents.py`, `deployments.py`) and include them in `main.py` via `APIRouter`.
*   **Error Handling**: Raise `HTTPException(status_code=..., detail=...)` for client errors. Keep business logic pure where possible.
*   **Typing**: Strictly use Python type hints (`list[str]`, `Optional[int]`, etc.).

### 3. Frontend (React / TypeScript)
*   **State Management**: Use `Zustand` (in `src/stores/`) instead of Context API or Redux. Keep stores modular.
*   **Components**: Use functional components with hooks. Maximize reusability. 
*   **UI Library**: Primarily use **Ant Design** (`antd`) components. Use **TailwindCSS** for layout and custom utility styling.
*   **Types**: Define strict interfaces for API responses and component props in `src/types/` or inline if specific to a file. 

## 🤖 AI Agent Specific Behaviors
1.  **Specification-Driven**: If creating a complex feature (e.g., Agent Gateway), first write a `docs/specs/*.md` file, wait for user approval, and then implement.
2.  **Mandatory UI Verification**: **Any UI/Frontend changes and modifications MUST be visually tested and verified using Playwright (via `webapp-testing` skill) or Chrome DevTools tools (`chrome-devtools_*`). You MUST take screenshots of the changes to verify the implementation is correct and to provide visual proof.**
3.  **Web Testing**: Utilize the `webapp-testing` skill (Playwright E2E via Python) or Chrome DevTools to visually test frontend changes if the Docker backend isn't available.
4.  **Read Before Write**: Always read the target file, relevant configuration (like `package.json` or `vite.config.ts`), and adjacent architecture docs (in `/docs/`) before making structural changes.
