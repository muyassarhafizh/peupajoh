# Run FastAPI server
serve:
	uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run FastAPI server with custom port
serve-port:
	uv run uvicorn app.main:app --reload --host 0.0.0.0 --port $(PORT)

# Install dependencies
install:
	uv sync

# Run main workflow test
main-workflow:
	uv run python -m usecase.main_workflow | tee output.log

# Format code
format:
	uv run ruff format .

# Lint code
lint:
	uv run ruff check .