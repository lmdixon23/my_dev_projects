# RAG Operations and Monitoring

A deployed retrieval system should record corpus version, embedding model, chunk settings, and index build time. Index freshness matters because updated documents do not affect answers until they are ingested. Changing an embedding model without rebuilding the stored vectors creates a dimension or representation mismatch.

Operational monitoring includes query latency, candidate counts, zero-hit rates, source distribution, and retrieval-quality checks on a fixed benchmark. Recall@3 can remain stable while MRR falls, indicating that relevant sources still appear but are ranked lower. Aggregate production clicks are not a substitute for labeled regression cases.

Reproducible incident analysis requires the exact query, configuration, index version, and retrieved source order. Access-control failures and stale data should be tracked separately from semantic retrieval failures because they require different remedies.
