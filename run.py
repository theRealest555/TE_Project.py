import uvicorn
from loguru import logger
from app.config import settings

if __name__ == "__main__":
    logger.info(f"Starting {settings.APP_NAME} server")
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)