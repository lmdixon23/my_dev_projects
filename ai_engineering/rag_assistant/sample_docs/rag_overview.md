# Retrieval-Augmented Generation

Retrieval-Augmented Generation (RAG) is a technique that improves the
quality of large language model output by grounding it in retrieved
documents from a knowledge base. Instead of relying only on the model's
parametric memory, the system first searches an index of documents,
selects the most relevant passages, and inserts them into the prompt
before generating an answer.

The core advantages of RAG are that it can cite sources, that it can be
updated by re-indexing rather than re-training, and that it dramatically
reduces hallucination on factual questions.

A typical RAG pipeline has four components: a document chunker that
splits long documents into overlapping windows, an embedder that turns
each chunk into a dense vector, a vector store that supports fast
nearest-neighbor search, and a generator that writes the final answer
conditioned on the retrieved context.
