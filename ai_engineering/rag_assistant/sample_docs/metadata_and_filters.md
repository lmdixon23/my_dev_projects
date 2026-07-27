# Metadata, Filters, and Isolation

Metadata can describe tenant, document type, language, publication date, access level, or product area. Pre-filtering restricts the searchable set before vector ranking. Post-filtering retrieves broadly and removes disallowed results afterward, which can leave too few candidates if the initial top-k is small.

Tenant isolation is an authorization boundary, not merely a relevance preference. A user must never retrieve another tenant's private chunks even when those chunks are semantically similar. Namespaces, access-control lists (ACLs), and mandatory metadata predicates can enforce that boundary.

Filters can improve precision by removing ineligible sources, but an incorrect or overly narrow predicate can destroy recall. Filter behavior should be tested with positive and negative cases, and the active filter expression should be recorded with retrieval traces.
