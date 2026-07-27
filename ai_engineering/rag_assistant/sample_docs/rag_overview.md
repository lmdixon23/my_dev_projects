# Retrieval-Augmented Generation

Retrieval-Augmented Generation (RAG) grounds a language model in external knowledge. The system searches an indexed corpus, selects relevant passages, inserts those passages into the prompt, and then asks the generator to answer from that context. Retrieval changes the evidence available to the model; generation turns that evidence into a response.

A typical RAG pipeline has four components. A chunker divides documents into retrieval units, an embedder maps each chunk and query to vectors, a vector store performs nearest-neighbor search, and a generator writes the final answer. Optional re-ranking can reorder retrieved candidates, but it does not replace the core four-stage path.

RAG can cite sources, reduce unsupported factual claims, and incorporate updated information by re-indexing documents rather than retraining the model. Those advantages depend on retrieval quality and index freshness. A citation shows where context came from, while separate evaluation is still needed to determine whether the answer is actually supported by that context.
