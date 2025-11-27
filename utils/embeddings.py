"""
Embedding generation and vector store management.
"""

import streamlit as st
from sentence_transformers import SentenceTransformer
import chromadb
from typing import List, Dict
import numpy as np


@st.cache_resource
def load_embedding_model():
    """
    Load sentence-transformers model.
    Cached to avoid reloading on every run.
    
    Returns:
        SentenceTransformer model
    """
    return SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')


def generate_embeddings(chunks: List[Dict], model: SentenceTransformer) -> np.ndarray:
    """
    Generate embeddings for text chunks.
    
    Args:
        chunks: List of chunk dictionaries with 'text' field
        model: SentenceTransformer model
    
    Returns:
        Numpy array of embeddings
    """
    texts = [chunk['text'] for chunk in chunks]
    embeddings = model.encode(texts, show_progress_bar=True)
    return embeddings


def create_vector_store(chunks_with_metadata: List[Dict], embeddings: np.ndarray):
    """
    Create in-memory ChromaDB collection.
    
    Args:
        chunks_with_metadata: List of chunk dicts with metadata
        embeddings: Numpy array of embeddings
    
    Returns:
        ChromaDB collection object
    """
    # Create in-memory ChromaDB client (updated for ChromaDB 0.5+)
    client = chromadb.Client()
    
    # Create or get collection
    collection_name = "thesis_chunks"
    
    # Delete if exists (for clean state)
    try:
        client.delete_collection(collection_name)
    except:
        pass
    
    collection = client.create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}
    )
    
    # Prepare data for insertion
    ids = [f"chunk_{chunk['chunk_id']}" for chunk in chunks_with_metadata]
    documents = [chunk['text'] for chunk in chunks_with_metadata]
    metadatas = [
        {
            'page_num': chunk['page_num'],
            'chunk_id': chunk['chunk_id'],
            'start_char': chunk.get('start_char', 0),
            'end_char': chunk.get('end_char', 0)
        }
        for chunk in chunks_with_metadata
    ]
    
    # Add to collection
    collection.add(
        ids=ids,
        embeddings=embeddings.tolist(),
        documents=documents,
        metadatas=metadatas
    )
    
    return collection


def retrieve_relevant_chunks(
    query: str,
    collection,
    model: SentenceTransformer,
    top_k: int = 5
) -> List[Dict]:
    """
    Retrieve most relevant chunks for a query.
    
    Args:
        query: Search query
        collection: ChromaDB collection
        model: SentenceTransformer model for query embedding
        top_k: Number of chunks to retrieve
    
    Returns:
        List of relevant chunks with metadata:
        [
            {
                'text': str,
                'page_num': int,
                'distance': float,
                'chunk_id': int
            }
        ]
    """
    # Generate query embedding
    query_embedding = model.encode([query])[0]
    
    # Query collection
    results = collection.query(
        query_embeddings=[query_embedding.tolist()],
        n_results=top_k
    )
    
    # Format results
    relevant_chunks = []
    
    if results['documents'] and len(results['documents']) > 0:
        for i in range(len(results['documents'][0])):
            relevant_chunks.append({
                'text': results['documents'][0][i],
                'page_num': results['metadatas'][0][i]['page_num'],
                'distance': results['distances'][0][i] if 'distances' in results else 0.0,
                'chunk_id': results['metadatas'][0][i]['chunk_id']
            })
    
    return relevant_chunks
