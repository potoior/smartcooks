
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.append(os.path.abspath("backend"))

from core.config import RAGConfig
from rag_modules import IndexConstructionModule, RetrievalOptimizationModule, DataPreparationModule
from langchain_core.documents import Document

def debug_retrieval():
    # Setup
    config = RAGConfig()
    # Correct path relative to project root
    config.data_path = os.path.join(os.path.abspath("backend"), "data")
    config.index_save_path = os.path.join(os.path.abspath("backend"), "vector_index")
    
    # Load raw documents to simulate chunks for BM25
    print("Loading documents...")
    data_module = DataPreparationModule(config.data_path)
    data_module.load_documents()
    chunks = data_module.chunk_documents()
    
    # Load index
    print("Loading index...")
    index_module = IndexConstructionModule(
        model_name=config.embedding_model,
        index_save_path=config.index_save_path
    )
    vectorstore = index_module.load_index()
    
    if not vectorstore:
        print("Error: Could not load vectorstore")
        return

    # Init Retrieval Module
    # Force low threshold to see what's actually there
    retrieval = RetrievalOptimizationModule(vectorstore, chunks, score_threshold=0.0)
    
    query = "我有胡萝卜，木耳，猪肉，我可以做什么菜"
    print(f"\nSearching for: {query}")
    
    # 1. Test Vector Search Raw
    print("\n--- Vector Search Results (Score Threshold=0.0) ---")
    vector_results = vectorstore.similarity_search_with_relevance_scores(query, k=10)
    for doc, score in vector_results:
        print(f"Score: {score:.4f} | Dish: {doc.metadata.get('dish_name')} | Content: {doc.page_content[:20]}...")

    # 2. Test BM25 Raw
    print("\n--- BM25 Search Results ---")
    bm25_results = retrieval.bm25_retriever.invoke(query)
    for i, doc in enumerate(bm25_results):
        print(f"Rank: {i+1} | Dish: {doc.metadata.get('dish_name')} | Content: {doc.page_content[:20]}...")

if __name__ == "__main__":
    debug_retrieval()
