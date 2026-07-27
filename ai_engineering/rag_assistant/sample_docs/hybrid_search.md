# Hybrid Search

Hybrid search combines dense semantic retrieval with lexical retrieval such as BM25. Dense vectors handle paraphrases and conceptual similarity. BM25 is often stronger for exact identifiers, rare names, acronyms, error codes, and other terms whose spelling matters.

Reciprocal rank fusion (RRF) merges ranked lists without requiring their raw scores to share a scale. Each document receives a contribution based on its rank in each list, and the fused score determines the combined ordering. Weighted score normalization is another option, but it requires more calibration.

Hybrid retrieval can add candidates that dense search missed. A later re-ranker may then reorder the fused pool. These are separate stages: fusion expands or combines retrieval evidence, while re-ranking performs a more expensive second-stage comparison over an existing pool.
