# Grounding and Citations

Grounding means constraining an answer to retrieved evidence. The prompt should identify each passage with a source label and tell the generator to distinguish supported statements from uncertainty. When retrieval returns no usable context, an empty-context guard should refuse a grounded answer instead of encouraging invention.

Citation presence is not the same as citation correctness. A response can attach a source label to a claim that the cited passage does not support. Evaluation should therefore separate retrieval quality, citation attribution, and answer faithfulness.

Source provenance helps a reader inspect the evidence and helps an operator trace failures. Good provenance includes the document source and, when useful, chunk identifiers or offsets. It does not compensate for a stale corpus, an access-control error, or a relevant passage that never entered the retrieved context.
