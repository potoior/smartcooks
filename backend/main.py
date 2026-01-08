"""
FastAPI 主应用
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from pathlib import Path

import sys
sys.path.append(str(Path(__file__).parent))

from api.routers.rag_router import router
from api.routers.upload_router import router as upload_router
from rag_system import RecipeRAGSystem

app = FastAPI(
    title="尝尝咸淡 RAG API",
    description="食谱检索增强生成系统 API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("正在初始化 RAG 系统...")
    # 由于RecipeRAGSystem现在是单例模式，这里会自动创建或获取唯一实例
    rag_system_instance = RecipeRAGSystem()
    print("RAG 系统初始化完成！")
    yield
    print("RAG 系统关闭")

app.router.lifespan_context = lifespan

app.include_router(router, prefix="/api", tags=["RAG"])
app.include_router(upload_router, prefix="/api", tags=["Upload"])

uploads_dir = Path("uploads")
uploads_dir.mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")


@app.get("/")
async def root():
    return {
        "message": "欢迎使用尝尝咸淡 RAG API",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)