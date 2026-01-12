"""
生成集成模块
"""

import os
import logging
from typing import List

from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.documents import Document
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

from core.prompts import PromptTemplates

logger = logging.getLogger(__name__)

class GenerationIntegrationModule:
    """生成集成模块 - 负责LLM集成和回答生成"""
    
    def __init__(self, model_name: str = "Qwen/Qwen2.5-7B-Instruct", temperature: float = 0.1, max_tokens: int = 2048):
        """
        初始化生成集成模块
        
        Args:
            model_name: 模型名称（硅基流动支持的模型）
            temperature: 生成温度
            max_tokens: 最大token数
        """
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.llm = None
        self.setup_llm()
    
    def setup_llm(self):
        """初始化大语言模型"""
        logger.info(f"正在初始化LLM: {self.model_name}")

        api_key = os.getenv("LLM_API_KEY")
        if not api_key:
            raise ValueError("请设置 LLM_API_KEY 环境变量")

        self.llm = ChatOpenAI(
            model=self.model_name,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            api_key=api_key,
            base_url=os.getenv("LLM_BASE_URL"),
            timeout=float(os.getenv("LLM_TIMEOUT", 60))
        )
        
        logger.info("LLM初始化完成")
    
    def generate_basic_answer(self, query: str, context_docs: List[Document], chat_history: str = "") -> str:
        """
        生成基础回答

        Args:
            query: 用户查询
            context_docs: 上下文文档列表
            chat_history: 聊天历史字符串

        Returns:
            生成的回答
        """
        context = self._build_context(context_docs)

        prompt = ChatPromptTemplate.from_template(PromptTemplates.BASIC_ANSWER_TEMPLATE)

        # 使用LCEL构建链
        chain = (
            {
                "question": RunnablePassthrough(), 
                "context": lambda _: context,
                "chat_history": lambda _: chat_history
            }
            | prompt
            | self.llm
            | StrOutputParser()
        )

        response = chain.invoke(query)
        return response
    
    def generate_step_by_step_answer(self, query: str, context_docs: List[Document], chat_history: str = "") -> str:
        """
        生成分步骤回答

        Args:
            query: 用户查询
            context_docs: 上下文文档列表
            chat_history: 聊天历史字符串

        Returns:
            分步骤的详细回答
        """
        context = self._build_context(context_docs)

        prompt = ChatPromptTemplate.from_template(PromptTemplates.STEP_BY_STEP_TEMPLATE)

        chain = (
            {
                "question": RunnablePassthrough(), 
                "context": lambda _: context,
                "chat_history": lambda _: chat_history
            }
            | prompt
            | self.llm
            | StrOutputParser()
        )

        response = chain.invoke(query)
        return response
    
    def query_rewrite(self, query: str, chat_history: str = "") -> str:
        """
        智能查询重写 - 让大模型判断是否需要重写查询

        Args:
            query: 原始查询
            chat_history: 聊天历史

        Returns:
            重写后的查询或原查询
        """
        prompt = PromptTemplate(
            template=PromptTemplates.QUERY_REWRITE_TEMPLATE,
            input_variables=["query", "chat_history"]
        )

        chain = (
            {
                "query": RunnablePassthrough(),
                "chat_history": lambda _: chat_history
            }
            | prompt
            | self.llm
            | StrOutputParser()
        )

        response = chain.invoke(query).strip()

        # 记录重写结果
        if response != query:
            logger.info(f"查询已重写: '{query}' → '{response}'")
        else:
            logger.info(f"查询无需重写: '{query}'")

        return response



    def query_router(self, query: str) -> str:
        """
        查询路由 - 根据查询类型选择不同的处理方式

        Args:
            query: 用户查询

        Returns:
            路由类型 ('list', 'detail', 'general')
        """
        prompt = ChatPromptTemplate.from_template(PromptTemplates.QUERY_ROUTER_TEMPLATE)

        chain = (
            {"query": RunnablePassthrough()}
            | prompt
            | self.llm
            | StrOutputParser()
        )

        result = chain.invoke(query).strip().lower()

        # 确保返回有效的路由类型
        if result in ['list', 'detail', 'general', 'chat']:
            return result
        else:
            return 'general'  # 默认类型

    def generate_list_answer(self, query: str, context_docs: List[Document]) -> str:
        """
        生成列表式回答 - 适用于推荐类查询

        Args:
            query: 用户查询
            context_docs: 上下文文档列表

        Returns:
            列表式回答
        """
        if not context_docs:
            return "抱歉，没有找到相关的菜品信息。"

        # 提取菜品名称
        dish_names = []
        for doc in context_docs:
            dish_name = doc.metadata.get('dish_name', '未知菜品')
            if dish_name not in dish_names:
                dish_names.append(dish_name)

        # 构建简洁的列表回答
        if len(dish_names) == 1:
            return f"为您推荐：{dish_names[0]}"
        elif len(dish_names) <= 3:
            return f"为您推荐以下菜品：\n" + "\n".join([f"{i+1}. {name}" for i, name in enumerate(dish_names)])
        else:
            return f"为您推荐以下菜品：\n" + "\n".join([f"{i+1}. {name}" for i, name in enumerate(dish_names[:3])]) + f"\n\n还有其他 {len(dish_names)-3} 道菜品可供选择。"

    async def generate_list_answer_stream(self, query: str, context_docs: List[Document]):
        """
        生成列表式回答 - 流式输出

        Args:
            query: 用户查询
            context_docs: 上下文文档列表

        Yields:
            生成的回答片段
        """
        if not context_docs:
            yield "抱歉，没有找到相关的菜品信息。"
            return

        # 提取菜品名称
        dish_names = []
        for doc in context_docs:
            dish_name = doc.metadata.get('dish_name', '未知菜品')
            if dish_name not in dish_names:
                dish_names.append(dish_name)

        # 构建简洁的列表回答
        if len(dish_names) == 1:
            yield f"为您推荐：{dish_names[0]}"
        elif len(dish_names) <= 3:
            response = f"为您推荐以下菜品：\n"
            yield response
            for i, name in enumerate(dish_names):
                yield f"{i+1}. {name}\n"
        else:
            response = f"为您推荐以下菜品：\n"
            yield response
            for i, name in enumerate(dish_names[:3]):
                yield f"{i+1}. {name}\n"
            yield f"\n还有其他 {len(dish_names)-3} 道菜品可供选择。"

    async def generate_basic_answer_stream(self, query: str, context_docs: List[Document], chat_history: str = ""):
        """
        生成基础回答 - 流式输出

        Args:
            query: 用户查询
            context_docs: 上下文文档列表
            chat_history: 聊天历史字符串

        Yields:
            生成的回答片段
        """
        context = self._build_context(context_docs)

        prompt = ChatPromptTemplate.from_template(PromptTemplates.BASIC_ANSWER_TEMPLATE)

        chain = (
            {
                "question": RunnablePassthrough(), 
                "context": lambda _: context,
                "chat_history": lambda _: chat_history
            }
            | prompt
            | self.llm
            | StrOutputParser()
        )

        async for chunk in chain.astream(query):
            yield chunk

    async def generate_step_by_step_answer_stream(self, query: str, context_docs: List[Document], chat_history: str = ""):
        """
        生成详细步骤回答 - 流式输出

        Args:
            query: 用户查询
            context_docs: 上下文文档列表
            chat_history: 聊天历史字符串

        Yields:
            详细步骤回答片段
        """
        context = self._build_context(context_docs)
        # print("context:", context)
        prompt = ChatPromptTemplate.from_template(PromptTemplates.STEP_BY_STEP_TEMPLATE)
        # print("prompt:", prompt)
        chain = (
            {
                "question": RunnablePassthrough(), 
                "context": lambda _: context,
                "chat_history": lambda _: chat_history
            }
            | prompt
            | self.llm
            | StrOutputParser()
        )

        async for chunk in chain.astream(query):
            yield chunk

    def generate_chat_answer(self, query: str, chat_history: str = "") -> str:
        """
        生成闲聊回答
        
        Args:
            query: 用户输入
            chat_history: 聊天历史

        Returns:
            回答
        """
        prompt = ChatPromptTemplate.from_template(PromptTemplates.CHAT_ANSWER_TEMPLATE)
        
        chain = (
            {
                "question": RunnablePassthrough(),
                "chat_history": lambda _: chat_history
            }
            | prompt
            | self.llm
            | StrOutputParser()
        )
        
        return chain.invoke(query)

    async def generate_chat_answer_stream(self, query: str, chat_history: str = ""):
        """
        生成闲聊回答 - 流式
        """
        prompt = ChatPromptTemplate.from_template(PromptTemplates.CHAT_ANSWER_TEMPLATE)
        
        chain = (
            {
                "question": RunnablePassthrough(),
                "chat_history": lambda _: chat_history
            }
            | prompt
            | self.llm
            | StrOutputParser()
        )
        
        async for chunk in chain.astream(query):
            yield chunk

    def _build_context(self, docs: List[Document], max_length: int = 2000) -> str:
        """
        构建上下文字符串
        
        Args:
            docs: 文档列表
            max_length: 最大长度
            
        Returns:
            格式化的上下文字符串
        """
        if not docs:
            return "暂无相关食谱信息。"
        
        context_parts = []
        current_length = 0
        
        for i, doc in enumerate(docs, 1):
            # 添加元数据信息
            metadata_info = f"【食谱 {i}】"
            if 'dish_name' in doc.metadata:
                metadata_info += f" {doc.metadata['dish_name']}"
            if 'category' in doc.metadata:
                metadata_info += f" | 分类: {doc.metadata['category']}"
            if 'difficulty' in doc.metadata:
                metadata_info += f" | 难度: {doc.metadata['difficulty']}"
            
            # 构建文档文本
            doc_text = f"{metadata_info}\n{doc.page_content}\n"
            
            # 检查长度限制
            if current_length + len(doc_text) > max_length:
                break
            
            context_parts.append(doc_text)
            current_length += len(doc_text)
        
        return "\n" + "="*50 + "\n".join(context_parts)