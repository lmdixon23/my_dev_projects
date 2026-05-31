# Vector Stores

A vector store indexes embeddings and answers nearest-neighbor queries.
FAISS is the most widely used in-process library; it offers exact search
(`IndexFlatIP`, `IndexFlatL2`) and several approximate indexes (HNSW,
IVF, PQ) with tunable speed-vs-recall tradeoffs.

For most projects under ten million chunks, an exact `IndexFlatIP`
index is fast enough and removes a whole class of tuning concerns. The
approximate indexes become attractive when memory or latency becomes
the constraint.

Hosted alternatives include Pinecone, Weaviate, Qdrant, and Chroma.
The right choice depends on whether you need multi-tenant isolation
(Pinecone), hybrid filtering (Weaviate), or a single-node experience
that just works (Chroma).
