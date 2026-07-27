# Vector Stores

A vector store indexes embeddings and answers nearest-neighbor queries. With L2-normalized vectors, an inner-product index ranks by cosine similarity. Exact indexes such as IndexFlatIP compare the query with every stored vector and avoid approximation error.

For many corpora below roughly ten million chunks, exact search can be fast enough and easier to reason about. Approximate nearest-neighbor (ANN) structures such as HNSW, IVF, and product quantization (PQ) trade some recall for lower latency or memory use. Their parameters should be tuned against a retrieval benchmark rather than selected only from throughput measurements.

Hosted systems such as Pinecone, Weaviate, Qdrant, and Chroma add operational features. Metadata filters, tenant isolation, replication, and hybrid-search support are separate concerns from the vector similarity algorithm itself. A filter that excludes the relevant document will reduce recall no matter how strong the embedding model is.
