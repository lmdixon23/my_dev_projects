# Embeddings, Briefly

An embedding is a vector representation of text. Semantically related passages should produce nearby vectors even when their wording differs. Sentence-transformers/all-MiniLM-L6-v2 is a common English retrieval baseline and produces 384-dimensional vectors.

Cosine similarity compares vector direction. L2-normalizing vectors at encoding time makes inner product equal cosine similarity, which allows a normalized corpus to use FAISS IndexFlatIP without recomputing vector norms for every query.

Model choice affects retrieval behavior. paraphrase-multilingual-MiniLM-L12-v2 is intended for multilingual corpora. Code-oriented search may benefit from an embedding model trained on source code and technical syntax. Embedding dimensions, preprocessing, and model version should be recorded with the index because changing any of them can make a saved store incompatible or invalidate a baseline.
