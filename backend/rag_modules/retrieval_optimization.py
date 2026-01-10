"""
检索优化模块
"""

import logging
from typing import List, Dict, Any

from langchain_community.vectorstores import FAISS
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document

logger = logging.getLogger(__name__)

class RetrievalOptimizationModule:
    """检索优化模块 - 负责混合检索和过滤"""
    
    def __init__(self, vectorstore: FAISS, chunks: List[Document], score_threshold: float = 0.4):
        """
        初始化检索优化模块
        
        Args:
            vectorstore: FAISS向量存储
            chunks: 文档块列表
            score_threshold: 检索阈值
        """
        self.vectorstore = vectorstore
        self.chunks = chunks
        self.score_threshold = score_threshold
        self.setup_retrievers()

    def setup_retrievers(self):
        """设置向量检索器和BM25检索器"""
        logger.info("正在设置检索器...")

        # 向量检索器 - 使用阈值过滤
        self.vector_retriever = self.vectorstore.as_retriever(
            search_type="similarity_score_threshold",
            search_kwargs={
                "k": 10,
                "score_threshold": self.score_threshold
            }
        )

        # BM25检索器 - 使用jieba分词
        def jieba_tokenizer(text: str) -> List[str]:
            import jieba
            return list(jieba.cut_for_search(text))

        self.bm25_retriever = BM25Retriever.from_documents(
            self.chunks,
            k=10,
            preprocess_func=jieba_tokenizer
        )



        logger.info("检索器设置完成")
    
    def hybrid_search(self, query: str, top_k: int = 3) -> List[Document]:
        """
        混合检索 - 结合向量检索和BM25检索，使用RRF重排

        Args:
            query: 查询文本
            top_k: 返回结果数量

        Returns:
            检索到的文档列表
        """
        # 分别获取向量检索和BM25检索结果（扩大搜索范围以便去重）
        vector_docs = self.vector_retriever.invoke(query)
        bm25_docs = self.bm25_retriever.invoke(query)

        print(f"\n[DEBUG] Query: {query}")
        print(f"[DEBUG] Vector Search Raw (len={len(vector_docs)}):")
        for i, doc in enumerate(vector_docs):
             score = "N/A"
             if hasattr(doc, 'metadata') and 'score' in doc.metadata:
                 score = doc.metadata['score']
             print(f"  {i+1}. {doc.metadata.get('dish_name')} (Score: {score})")
             
        print(f"[DEBUG] BM25 Search Raw (len={len(bm25_docs)}):")
        for i, doc in enumerate(bm25_docs):
            print(f"  {i+1}. {doc.metadata.get('dish_name')}")

        # 去重：每个菜品只保留得分最高的一个chunk
        vector_docs = self._deduplicate_by_parent(vector_docs)
        bm25_docs = self._deduplicate_by_parent(bm25_docs)
        
        print(f"[DEBUG] Vector Search Deduplicated: {[d.metadata.get('dish_name') for d in vector_docs]}")
        print(f"[DEBUG] BM25 Search Deduplicated: {[d.metadata.get('dish_name') for d in bm25_docs]}")

        # 使用RRF重排
        reranked_docs = self._rrf_rerank(vector_docs, bm25_docs)
        return reranked_docs[:top_k]

    def _deduplicate_by_parent(self, docs: List[Document]) -> List[Document]:
        """
        按父文档(菜品)去重，保留排名最靠前的chunk
        """
        seen_parents = set()
        unique_docs = []
        
        for doc in docs:
            # 优先使用 parent_id，如果没有则使用 dish_name
            parent_id = doc.metadata.get('parent_id') or doc.metadata.get('dish_name')
            
            if parent_id and parent_id not in seen_parents:
                seen_parents.add(parent_id)
                unique_docs.append(doc)
            elif not parent_id:
                # 如果没有标识符，则保留（保守策略）
                unique_docs.append(doc)
                
        return unique_docs
    
    def _rrf_rerank(self, vector_docs: List[Document], bm25_docs: List[Document], k: int = 60) -> List[Document]:
        """
        带元数据过滤的检索
        
        Args:
            query: 查询文本
            filters: 元数据过滤条件
            top_k: 返回结果数量
            
        Returns:
            过滤后的文档列表
        """
        # 先进行混合检索，获取更多候选
        docs = self.hybrid_search(query, top_k * 3)
        
        # 应用元数据过滤
        filtered_docs = []
        for doc in docs:
            match = True
            for key, value in filters.items():
                if key in doc.metadata:
                    if isinstance(value, list):
                        if doc.metadata[key] not in value:
                            match = False
                            break
                    else:
                        if doc.metadata[key] != value:
                            match = False
                            break
                else:
                    match = False
                    break
            
            if match:
                filtered_docs.append(doc)
                if len(filtered_docs) >= top_k:
                    break
        
        return filtered_docs

    def _rrf_rerank(self, vector_docs: List[Document], bm25_docs: List[Document], k: int = 60, weights: Dict[str, float] = None) -> List[Document]:
        """
        使用加权RRF算法重排文档
        weights: {"vector": 2.0, "bm25": 0.5}
        """
        if weights is None:
            weights = {"vector": 3.0, "bm25": 0.5}  # 提高向量检索权重，降低BM25权重

        doc_scores = {}
        doc_objects = {}

        # 计算向量检索结果的RRF分数
        for rank, doc in enumerate(vector_docs):
            # 使用文档内容的哈希作为唯一标识
            doc_id = hash(doc.page_content)
            doc_objects[doc_id] = doc

            # RRF公式: weight * (1 / (k + rank))
            rrf_score = weights["vector"] * (1.0 / (k + rank + 1))
            doc_scores[doc_id] = doc_scores.get(doc_id, 0) + rrf_score

            logger.debug(f"向量检索 - 文档{rank+1}: RRF分数 = {rrf_score:.4f}")

        # 计算BM25检索结果的RRF分数
        for rank, doc in enumerate(bm25_docs):
            doc_id = hash(doc.page_content)
            doc_objects[doc_id] = doc

            rrf_score = weights["bm25"] * (1.0 / (k + rank + 1))
            doc_scores[doc_id] = doc_scores.get(doc_id, 0) + rrf_score

            logger.debug(f"BM25检索 - 文档{rank+1}: RRF分数 = {rrf_score:.4f}")

        # 按最终RRF分数排序
        sorted_docs = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)

        # 构建最终结果
        reranked_docs = []
        for doc_id, final_score in sorted_docs:
            if doc_id in doc_objects:
                doc = doc_objects[doc_id]
                # 将RRF分数添加到文档元数据中
                doc.metadata['rrf_score'] = final_score
                reranked_docs.append(doc)
                logger.debug(f"最终排序 - 文档: {doc.page_content[:50]}... 最终RRF分数: {final_score:.4f}")

        logger.info(f"RRF重排完成: 向量检索{len(vector_docs)}个文档, BM25检索{len(bm25_docs)}个文档, 合并后{len(reranked_docs)}个文档")

        return reranked_docs
