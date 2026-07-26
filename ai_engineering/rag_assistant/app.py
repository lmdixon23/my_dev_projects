"""Flask serving layer for the RAG pipeline.

POST /ask {"question": "..."} -> {"answer", "sources", "tokens_used"}
GET  /health                  -> {"status": "ok", "chunks": N}

Build with `build_app("./index")` so a saved store is loaded once at
startup and reused across requests (no per-request rebuild).
Set RERANKER_MODEL to opt into cross-encoder re-ranking.
"""

from __future__ import annotations

import os

from flask import Flask, jsonify, request

from rag import CrossEncoderReranker, RAGPipeline


def build_app(store_path: str) -> Flask:
    app = Flask(__name__)
    reranker_model = os.environ.get("RERANKER_MODEL", "").strip()
    reranker = (
        CrossEncoderReranker(model_name=reranker_model)
        if reranker_model
        else None
    )
    candidate_k = int(os.environ.get("RERANKER_CANDIDATES", "20"))
    pipeline = RAGPipeline.load(
        store_path,
        reranker=reranker,
        candidate_k=candidate_k,
    )

    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok", "chunks": len(pipeline.store)})

    @app.route("/ask", methods=["POST"])
    def ask():
        body = request.get_json(silent=True) or {}
        question = body.get("question")
        if not isinstance(question, str) or not question.strip():
            return jsonify({"error": "Provide 'question' (non-empty string)."}), 400
        k = int(body.get("k", 5))
        result = pipeline.ask(question, k=k)
        return jsonify({
            "answer": result.answer,
            "sources": result.sources,
            "tokens_used": result.tokens_used,
            "retrieved": [
                {
                    "score": r.score,
                    "retrieval_score": r.retrieval_score,
                    "source": r.chunk.source,
                    "chunk_index": r.chunk.chunk_index,
                }
                for r in result.retrieved
            ],
        })

    return app


if __name__ == "__main__":
    store_path = os.environ.get("RAG_STORE", "./index")
    build_app(store_path).run(host="0.0.0.0", port=int(os.environ.get("PORT", "8080")))
