import os

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from api.router import router as router_api
from config import settings


app = FastAPI()
# Добавляем middleware для CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Разрешаем все источники
    allow_credentials=True,
    allow_methods=["*"],  # Разрешаем все методы
    allow_headers=["*"],  # Разрешаем все заголовки
)
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)


app.mount("/files", StaticFiles(directory=settings.UPLOAD_DIR), name="files")
app.mount("/static", StaticFiles(directory=settings.STATIC_DIR), name="static")


app.include_router(router_api)


if __name__ == "__main__":
    uvicorn.run("main:app", host='127.0.0.1', port=8000, reload=True)
