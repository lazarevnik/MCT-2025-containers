import uvicorn
from app.config import settings


if __name__ == "__main__":
    uvicorn.run(
        "app.api:api",
        forwarded_allow_ips="*",
        host="0.0.0.0",
        port=settings.APP_PORT,
    )
