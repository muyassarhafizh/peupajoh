"""Simple script to run the FastAPI server."""

import uvicorn
import os

if __name__ == "__main__":
    # Configuration
    host = os.getenv("APP_HOST", "0.0.0.0")
    port = int(os.getenv("APP_PORT", "8000"))
    reload = os.getenv("APP_RELOAD", "true").lower() == "true"

    print("Starting Peupajoh API server...")
    print(f"Server: http://{host}:{port}")
    print(f"API Docs: http://{host}:{port}/api/docs")
    print(f"ReDoc: http://{host}:{port}/api/redoc")
    print(f"Reload: {reload}")
    print()

    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=reload,
    )
