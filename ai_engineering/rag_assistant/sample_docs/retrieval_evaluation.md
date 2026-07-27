# Retrieval Evaluation

Retrieval evaluation compares ranked results with labeled relevant sources. Recall@1 is the fraction of questions with an acceptable source in the first position. Recall@3 asks whether an acceptable source appears anywhere in the first three results. Mean reciprocal rank (MRR) averages 1 divided by the rank of the first relevant result, assigning zero when no relevant source is retrieved.

A case may name more than one acceptable source when several documents contain sufficient evidence. Per-case output is needed to diagnose individual failures. Category slices reveal whether an aggregate score hides regressions on paraphrases, terminology variants, cross-chunk questions, or hard negatives.

A deterministic baseline is a comparison instrument, not a leaderboard claim. Future changes should run against the same versioned corpus, case labels, chunk settings, and embedder. A practical regression rule allows small numerical variation while rejecting material losses in recall@3, MRR, or a required category slice.
