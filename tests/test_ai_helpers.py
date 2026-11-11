import json
import os
import tempfile
import unittest
from unittest.mock import patch

from docx import Document
from io import BytesIO
from pypdf import PdfWriter

from utils import ai, documents, storage


class AIHelperTests(unittest.TestCase):
    def setUp(self):
        self.groq_key = patch.dict(os.environ, {"GROQ_API_KEY": "test-groq-key"})
        self.gemini_key = patch.dict(os.environ, {"GEMINI_API_KEY": "test-gemini-key"})
        self.groq_key.start()
        self.gemini_key.start()
        self.addCleanup(self.groq_key.stop)
        self.addCleanup(self.gemini_key.stop)

    @patch("utils.ai.requests.post")
    def test_groq_chat_json_parses_fenced_json_object(self, post):
        post.return_value.ok = True
        post.return_value.json.return_value = {
            "choices": [{"message": {"content": '```json\n{"skills":["Python"]}\n```'}}]
        }
        self.assertEqual(
            ai.groq_chat_json([{"role": "user", "content": "parse"}]),
            {"skills": ["Python"]},
        )
        self.assertEqual(post.call_args.kwargs["headers"]["Authorization"], "Bearer test-groq-key")

    @patch("utils.ai.requests.post")
    def test_gemini_embeddings_batches_and_checks_response(self, post):
        post.return_value.ok = True
        post.return_value.json.return_value = {
            "embeddings": [{"values": [1.0, 0.0]}, {"values": [0.0, 1.0]}]
        }
        vectors = ai.gemini_embeddings(["resume", "job"], "RETRIEVAL_DOCUMENT")
        self.assertEqual(vectors, [[1.0, 0.0], [0.0, 1.0]])
        self.assertEqual(len(post.call_args.kwargs["json"]["requests"]), 2)
        self.assertEqual(ai.cosine_similarity(vectors[0], vectors[1]), 0.0)

    def test_cosine_similarity_handles_zero_vectors(self):
        self.assertEqual(ai.cosine_similarity([0.0, 0.0], [1.0, 0.0]), 0.0)
        with self.assertRaises(ValueError):
            ai.cosine_similarity([1.0], [1.0, 0.0])


class ResumeExtractionTests(unittest.TestCase):
    def test_extracts_docx_paragraphs_and_table_cells(self):
        document = Document()
        document.add_paragraph("Software engineer with Python experience")
        table = document.add_table(rows=1, cols=2)
        table.cell(0, 0).text = "Education"
        table.cell(0, 1).text = "BSc Computer Science"
        content = BytesIO()
        document.save(content)

        text = documents.extract_resume_text("resume.docx", content.getvalue())
        self.assertIn("Python experience", text)
        self.assertIn("BSc Computer Science", text)

    def test_rejects_unsupported_and_oversized_files(self):
        with self.assertRaisesRegex(ValueError, "PDF or DOCX"):
            documents.extract_resume_text("resume.txt", b"plain text")
        with self.assertRaisesRegex(ValueError, "10 MB"):
            documents.extract_resume_text("resume.pdf", b"x" * (10 * 1024 * 1024 + 1))

    def test_rejects_pdf_without_extractable_text(self):
        writer = PdfWriter()
        writer.add_blank_page(width=72, height=72)
        content = BytesIO()
        writer.write(content)
        with self.assertRaisesRegex(ValueError, "No readable text"):
            documents.extract_resume_text("resume.pdf", content.getvalue())


class ActivityStorageTests(unittest.TestCase):
    def test_records_recent_activity_without_resume_content(self):
        with tempfile.TemporaryDirectory() as directory:
            activity_path = os.path.join(directory, "activity.json")
            with patch.object(storage, "ACTIVITY_FILE", activity_path):
                storage.record_activity(
                    "resume_score",
                    "Scored a resume",
                    "Overall match: 8/10",
                    8,
                )
                events = storage.load_activity()
            self.assertEqual(events[0]["kind"], "resume_score")
            self.assertEqual(events[0]["score"], 8)
            self.assertNotIn("private candidate text", json.dumps(events).lower())

    def test_reports_corrupt_activity_data(self):
        with tempfile.TemporaryDirectory() as directory:
            activity_path = os.path.join(directory, "activity.json")
            with open(activity_path, "w", encoding="utf-8") as f:
                f.write("not-json")
            with patch.object(storage, "ACTIVITY_FILE", activity_path):
                with self.assertRaisesRegex(RuntimeError, "Could not read activity log"):
                    storage.load_activity()


if __name__ == "__main__":
    unittest.main()
