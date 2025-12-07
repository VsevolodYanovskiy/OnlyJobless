import uvicorn
import logging
import asyncio
from src.back.setup.app import create_application


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

app = create_application()

if __name__ == "__main__":
    uv_config = uvicorn.Config(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
        loop="asyncio",
        http="httptools",
        ws="websockets",
        timeout_keep_alive=30
    )
    server = uvicorn.Server(uv_config)
    asyncio.run(server.serve())
