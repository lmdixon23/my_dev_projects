import unittest

from rag.chunker import Chunker, Document


class TestChunker(unittest.TestCase):
    def test_short_doc_is_one_chunk(self):
        doc = Document(source="x.md", text="A short paragraph.")
        chunks = Chunker().chunk_document(doc, doc_id="d0")
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0].chunk_id, "d0#0")
        self.assertEqual(chunks[0].source, "x.md")

    def test_paragraph_packing_respects_chunk_size(self):
        paras = "\n\n".join(["abc def ghi"] * 20)
        doc = Document(source="x.md", text=paras)
        chunks = Chunker(chunk_size=50, chunk_overlap=10).chunk_document(doc, doc_id="d0")
        self.assertGreater(len(chunks), 1)
        for c in chunks:
            # Allow overlap to push a chunk slightly past chunk_size in edge cases.
            self.assertLessEqual(len(c.text), 60)

    def test_very_long_paragraph_is_sentence_split(self):
        long_para = " ".join([f"Sentence number {i}." for i in range(40)])
        doc = Document(source="x.md", text=long_para)
        chunks = Chunker(chunk_size=80, chunk_overlap=10).chunk_document(doc, doc_id="d0")
        self.assertGreater(len(chunks), 1)

    def test_overlap_must_be_less_than_chunk_size(self):
        with self.assertRaises(ValueError):
            Chunker(chunk_size=10, chunk_overlap=10)


if __name__ == "__main__":
    unittest.main()
