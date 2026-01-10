"""
RAG 系统包装类 - 用于 FastAPI
"""

import os
import threading
from pathlib import Path
from dotenv import load_dotenv
from fastapi.responses import StreamingResponse
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

from core.config import DEFAULT_CONFIG, RAGConfig
from rag_modules import (
    DataPreparationModule,
    IndexConstructionModule,
    RetrievalOptimizationModule,
    GenerationIntegrationModule
)

load_dotenv()


class RecipeRAGSystem:
    """食谱RAG系统包装类"""
    # 单例模式相关属性
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, config: RAGConfig = None):
        """实现线程安全的单例模式"""
        if cls._instance is None:
            with cls._lock:
                # 双重检查，确保线程安全
                if cls._instance is None:
                    cls._instance = super(RecipeRAGSystem, cls).__new__(cls)
        return cls._instance

    def __init__(self, config: RAGConfig = None, force_reinit: bool = False):
        # 确保只初始化一次，除非强制重新初始化
        if hasattr(self, '_initialized') and not force_reinit:
            return

        self.config = config or DEFAULT_CONFIG
        self.data_module = None
        self.index_module = None
        self.retrieval_module = None
        self.generation_module = None
        # 开始初始化数据准备模块
        self.initialize_system()
        print("="*30)
        if not Path(self.config.data_path).exists():
            # 初始化构建索引向量
            print(f"数据路径不存在: {self.config.data_path},开始构建索引")

        if not os.getenv("LLM_API_KEY"):
            raise ValueError("请设置 LLM_API_KEY 环境变量")
        print("开始构建知识库")
        self.build_knowledge_base()
        print("知识库构建完成")
        
        # 标记为已初始化
        self._initialized = True


    def initialize_system(self):
        """初始化所有模块"""
        print("初始化数据准备模块...")
        self.data_module = DataPreparationModule(self.config.data_path)
        print("数据准备模块初始化完成")
        print("初始化索引构建模块...")
        self.index_module = IndexConstructionModule(
            model_name=self.config.embedding_model,
            index_save_path=self.config.index_save_path
        )
        print("索引构建模块初始化完成")
        print("🤖 初始化生成集成模块...")
        self.generation_module = GenerationIntegrationModule(
            model_name=self.config.llm_model,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens
        )
        print("生成集成模块初始化完成")
        print("初始化完成")

    def build_knowledge_base(self):
        """构建知识库"""
        print("开始构建知识库...")
        vectorstore = self.index_module.load_index()

        if vectorstore is not None:
            print("✅ 成功加载已保存的向量索引！")
            # 仍需要加载文档和分块用于检索模块
            print("加载食谱文档...")
            self.data_module.load_documents()
            print("进行文本分块...")
            chunks = self.data_module.chunk_documents()
        else:
            print("未找到已保存的索引，开始构建新索引...")
            # 2. 加载文档
            print("加载食谱文档...")
            self.data_module.load_documents()
            # 3. 文本分块
            print("进行文本分块...")
            chunks = self.data_module.chunk_documents()
            # 4. 构建向量索引
            print("构建向量索引...")
            vectorstore = self.index_module.build_vector_index(chunks)
            # 5. 保存索引
            print("保存向量索引...")
            self.index_module.save_index()

        print("初始化检索优化...")
        self.retrieval_module = RetrievalOptimizationModule(
            self.index_module.vectorstore,
            self.data_module.chunks,
            score_threshold=self.config.score_threshold,
            rrf_weights=self.config.rrf_weights
        )

        stats = self.data_module.get_statistics()
        print(f"\n📊 知识库统计:")
        print(f"   文档总数: {stats['total_documents']}")
        print(f"   文本块数: {stats['total_chunks']}")
        print(f"   菜品分类: {list(stats['categories'].keys())}")
        print(f"   难度分布: {stats['difficulties']}")

        print("✅ 知识库构建完成！")

    def get_statistics(self):
        """获取知识库统计信息"""
        return self.data_module.get_statistics()

    def ask_question(self, question: str, chat_history: list = None, stream: bool = True):
        """回答用户问题"""
        
        # 格式化聊天历史
        chat_history_str = ""
        if chat_history:
            history_parts = []
            for msg in chat_history[-6:]: # 只取最近6条
                role_name = "用户" if msg.get("role") == "user" else "助手"
                content = msg.get("content", "")
                history_parts.append(f"{role_name}: {content}")
            chat_history_str = "\n".join(history_parts)

        if not all([self.retrieval_module, self.generation_module]):
            raise ValueError("请先构建知识库")
        print(f"开始处理问题:{question},当前的stream为{stream}")
        route_type = self.generation_module.query_router(question)


        print(f"路由结果: {route_type}")

        # 如果是闲聊，直接生成不需要检索
        if route_type == 'chat':
            if stream:
                async def generate():
                    answer_chunks = self.generation_module.generate_chat_answer_stream(question, chat_history=chat_history_str)
                    async for chunk in answer_chunks:
                        row = {
                            "answer": chunk,
                            "documents": [],
                            "route_type": "chat"
                        }
                        yield row
                
                return generate()
            else:
                answer = self.generation_module.generate_chat_answer(question, chat_history=chat_history_str)
                return {
                    "answer": answer,
                    "documents": [],
                    "route_type": "chat"
                }

        # 优化查询（仅非闲聊）
        rewritten_query = self.generation_module.query_rewrite(question)

        filters = self._extract_filters_from_query(question)
        if filters:
            relevant_chunks = self.retrieval_module.metadata_filtered_search(
                rewritten_query, filters, top_k=self.config.top_k
            )
        else:
            relevant_chunks = self.retrieval_module.hybrid_search(
                rewritten_query, top_k=self.config.top_k
            )

        if not relevant_chunks:
            if stream:
                async def empty_generator():
                    yield {
                        "answer": "抱歉，没有找到相关的食谱信息。请尝试其他菜品名称或关键词。",
                        "route_type": route_type,
                        "documents": []
                    }
                return empty_generator()
            else:
                return {
                    "answer": "抱歉，没有找到相关的食谱信息。请尝试其他菜品名称或关键词。",
                    "route_type": route_type,
                    "documents": []
                }

        relevant_docs = self.data_module.get_parent_documents(relevant_chunks)

        doc_info = []
        for doc in relevant_docs:
            doc_info.append({
                "dish_name": doc.metadata.get('dish_name', '未知菜品'),
                "category": doc.metadata.get('category', '未知'),
                "difficulty": doc.metadata.get('difficulty', '未知')
            })

        if stream:
            async def stream_generator():
                if route_type == 'list':
                    answer_chunks = self.generation_module.generate_list_answer_stream(question, relevant_docs)
                elif route_type == "detail":
                    answer_chunks = self.generation_module.generate_step_by_step_answer_stream(question, relevant_docs, chat_history=chat_history_str)
                else:
                    answer_chunks = self.generation_module.generate_basic_answer_stream(question, relevant_docs, chat_history=chat_history_str)
                
                async for chunk in answer_chunks:
                    row = {
                        "answer": chunk,
                        "route_type": route_type,
                        "documents": doc_info
                    }
                    yield row
            
            return stream_generator()
        else:
            if route_type == 'list':
                answer = self.generation_module.generate_list_answer(question, relevant_docs)
            elif route_type == "detail":
                answer = self.generation_module.generate_step_by_step_answer(question, relevant_docs, chat_history=chat_history_str)
            else:
                answer = self.generation_module.generate_basic_answer(question, relevant_docs, chat_history=chat_history_str)

            return {
                "answer": answer,
                "route_type": route_type,
                "documents": doc_info
            }

    def search_by_category(self, category: str, query: str = ""):
        """按分类搜索菜品"""
        if not self.retrieval_module:
            raise ValueError("请先构建知识库")

        search_query = query if query else category
        filters = {"category": category}

        docs = self.retrieval_module.metadata_filtered_search(search_query, filters, top_k=10)

        dish_names = []
        for doc in docs:
            dish_name = doc.metadata.get('dish_name', '未知菜品')
            if dish_name not in dish_names:
                dish_names.append(dish_name)

        return dish_names

    def _extract_filters_from_query(self, query: str) -> dict:
        """从用户问题中提取元数据过滤条件"""
        filters = {}
        category_keywords = DataPreparationModule.get_supported_categories()
        for cat in category_keywords:
            if cat in query:
                filters['category'] = cat
                break

        difficulty_keywords = DataPreparationModule.get_supported_difficulties()
        for diff in sorted(difficulty_keywords, key=len, reverse=True):
            if diff in query:
                filters['difficulty'] = diff
                break

        return filters