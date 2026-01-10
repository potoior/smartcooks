
import os
import sys
import jieba
from pathlib import Path
from langchain_core.documents import Document

# Add backend to path
sys.path.append(os.path.abspath("backend"))

from core.config import RAGConfig
from rag_modules import IndexConstructionModule, RetrievalOptimizationModule, DataPreparationModule

def debug_comparison():
    # Setup
    config = RAGConfig()
    config.data_path = os.path.join(os.path.abspath("backend"), "data")
    config.index_save_path = os.path.join(os.path.abspath("backend"), "vector_index")
    config.top_k = 5
    
    # Load Documents
    print("Loading documents...")
    data_module = DataPreparationModule(config.data_path)
    data_module.load_documents()
    chunks = data_module.chunk_documents()
    
    # Load Index
    print("Loading index...")
    index_module = IndexConstructionModule(
        model_name=config.embedding_model,
        index_save_path=config.index_save_path
    )
    vectorstore = index_module.load_index()
    
    # Init Retrieval
    retrieval = RetrievalOptimizationModule(
        vectorstore, 
        chunks, 
        score_threshold=config.score_threshold
    )
    
    queries = [
        "我有猪肉、胡萝卜、木耳可以做什么",
        "我有胡萝卜和猪肉以及木耳可以做什么"
    ]
    
    for query in queries:
        print(f"\n{'='*50}")
        print(f"Query: {query}")
        print(f"{'='*50}")
        
        # 1. Check Tokenization
        tokens = list(jieba.cut_for_search(query))
        print(f"[Tokens]: {tokens}")
        
        # 2. Hybrid Search (which prints debug logs)
        results = retrieval.hybrid_search(query, top_k=5)
        
        print("\n[Final Results]:")
        for i, doc in enumerate(results):
            dish = doc.metadata.get('dish_name')
            score = doc.metadata.get('rrf_score', 0)
            print(f"{i+1}. {dish} (RRF: {score:.4f})")

if __name__ == "__main__":
    debug_comparison()
