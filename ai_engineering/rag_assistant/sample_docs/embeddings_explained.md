# Embeddings, Briefly

An embedding is a vector representation of a piece of text such that
semantically similar texts produce vectors that are close together
under a chosen distance metric, usually cosine similarity. Modern
sentence embedding models like `sentence-transformers/all-MiniLM-L6-v2`
produce 384-dimensional vectors that work well for retrieval out of the
box.

When using cosine similarity it is convenient to L2-normalize the
vectors at encoding time so that the inner product equals the cosine.
This lets you use a FAISS `IndexFlatIP` (inner product) index directly
without computing norms at query time.

Embedding model choice matters most for retrieval quality. A 384-d
MiniLM model is a strong default. For multilingual corpora, the
`paraphrase-multilingual-MiniLM-L12-v2` model is the natural choice.
For code search, `text-embedding-3-small` from OpenAI handles syntax
better than general-purpose sentence models.
