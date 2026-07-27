# Chunking Strategies

Chunking determines the text units that retrieval can return. Paragraph-first splitting preserves local structure, while sentence fallback prevents a single long paragraph from becoming an oversized chunk. Character-based limits are model-agnostic; token-aware limits align more directly with model context windows.

Chunks that are too small lose surrounding definitions and qualifiers. Chunks that are too large mix unrelated topics and dilute the embedding signal. Overlap carries a boundary region into the next chunk so a statement split near an edge can still be retrieved with its nearby context.

Cross-chunk questions expose a common failure mode. One paragraph may define a concept while the next paragraph states an exception or operating condition. Increasing overlap can help, but excessive overlap creates near-duplicate candidates and wastes index space. Chunk size and overlap should therefore be versioned and compared on the same labeled benchmark.
