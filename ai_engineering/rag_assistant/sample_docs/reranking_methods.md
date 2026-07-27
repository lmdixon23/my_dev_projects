# Re-ranking Methods

A re-ranker receives a candidate pool from an initial retriever and assigns new relevance scores. A cross-encoder reads the query and candidate passage together, which is slower than a bi-encoder but can model detailed interactions between their words.

Re-ranking changes the order of candidates already present. It cannot recover a relevant passage that the embedding retriever omitted from the candidate pool. Candidate-k therefore controls a quality-latency tradeoff: a larger pool gives the re-ranker more opportunities, while a smaller pool reduces scoring cost.

The final top-k should preserve score provenance. Recording both the original retrieval score and the re-ranker score makes debugging possible. Re-ranking is different from hybrid search: hybrid retrieval can introduce candidates from a lexical system, whereas a re-ranker only reorders the candidates it receives.
