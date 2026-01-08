from pathlib import Path
from typing import Optional, List, Dict, Any
import sys

sys.path.append(str(Path(__file__).parent.parent))
from core.rag_system import RecipeRAGSystem


class RAGService:
    """RAG 服务层"""
    
    def __init__(self):
        self.rag = RecipeRAGSystem()
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取知识库统计信息"""
        return self.rag.get_statistics()
    
    def ask_question(
        self, 
        question: str, 
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        提问接口
        
        Args:
            question: 用户问题
            stream: 是否流式返回
            
        Returns:
            回答结果
        """
        return self.rag.ask_question(question, stream=stream)
    
    def search_by_category(
        self, 
        category: str, 
        query: str = ""
    ) -> List[Dict[str, Any]]:
        """
        按分类搜索菜品
        
        Args:
            category: 分类名称
            query: 搜索关键词
            
        Returns:
            菜品列表
        """
        return self.rag.search_by_category(category, query)
    
    def get_categories(self) -> List[str]:
        """获取支持的分类列表"""
        from rag_modules import DataPreparationModule
        return DataPreparationModule.get_supported_categories()
    
    def get_difficulties(self) -> List[str]:
        """获取支持的难度列表"""
        from rag_modules import DataPreparationModule
        return DataPreparationModule.get_supported_difficulties()
    
    def ask_with_image(
        self, 
        question: str, 
        image_name: Optional[str] = None
    ) -> str:
        """
        带图片的提问
        
        Args:
            question: 用户问题
            image_name: 图片文件名
            
        Returns:
            处理后的问题
        """
        if not image_name:
            return question
        
        from services.image_service import ImageService
        image_service = ImageService()
        
        image_path = Path("uploads") / image_name
        if not image_path.exists():
            raise ValueError("图片不存在")
        
        food_name = image_service.recognize_food(image_path)
        
        if food_name == "没有食材":
            raise ValueError("图片中没有食材")
        
        return f"我有{food_name},{question}"
