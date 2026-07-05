import logging
import re
import numpy as np
from typing import List

logger = logging.getLogger(__name__)

class RAGProcessor:
    def __init__(self):
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("SentenceTransformer loaded for RAG Processor.")
        except Exception as e:
            logger.error(f"Failed to load SentenceTransformer: {e}")
            self.model = None

    def chunk_text(self, text: str, max_chars: int = 600, overlap: int = 100) -> List[str]:
        """Split text into overlapping chunks for semantic processing."""
        # Clean text
        text = re.sub(r'\s+', ' ', text).strip()
        chunks = []
        start = 0
        while start < len(text):
            end = start + max_chars
            if end >= len(text):
                chunks.append(text[start:])
                break
            
            # Try to find a sentence boundary
            match = re.search(r'[.!?]\s+', text[end-100:end+100])
            if match:
                end = (end - 100) + match.end()
            
            chunks.append(text[start:end].strip())
            start = end - overlap
        return [c for c in chunks if len(c) > 50] # filter very short chunks

    def condense_text(self, text: str, max_output_chars: int = 15000) -> str:
        """
        Uses clustering to extract the most representative diverse chunks.
        """
        if not self.model:
            logger.warning("RAG model not loaded, returning truncated text.")
            return text[:max_output_chars]

        if len(text) <= max_output_chars:
            return text
            
        chunks = self.chunk_text(text)
        if not chunks:
            return ""
            
        try:
            from sklearn.cluster import KMeans
            from sklearn.metrics import pairwise_distances_argmin_min
            
            # Embed all chunks
            embeddings = self.model.encode(chunks)
            
            # Determine number of clusters based on desired output size
            # Assume average chunk is 500 chars
            avg_chunk_size = sum(len(c) for c in chunks) / len(chunks)
            num_clusters = max(2, min(len(chunks), int(max_output_chars / avg_chunk_size)))
            
            if num_clusters >= len(chunks):
                return "\n\n".join(chunks)

            # Cluster the embeddings to find diverse topics
            kmeans = KMeans(n_clusters=num_clusters, random_state=42, n_init="auto")
            kmeans.fit(embeddings)
            
            # Find the chunk closest to each cluster centroid
            closest_indices, _ = pairwise_distances_argmin_min(kmeans.cluster_centers_, embeddings)
            
            # Sort indices to maintain original reading order
            selected_indices = sorted(list(closest_indices))
            
            selected_chunks = [chunks[i] for i in selected_indices]
            logger.info(f"Condensed document from {len(chunks)} chunks down to {len(selected_chunks)} representative chunks.")
            
            return "\n\n".join(selected_chunks)
            
        except Exception as e:
            logger.error(f"Clustering failed: {e}")
            return text[:max_output_chars]

# Singleton instance
rag_processor = None
def get_rag_processor():
    global rag_processor
    if rag_processor is None:
        rag_processor = RAGProcessor()
    return rag_processor
