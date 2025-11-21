import io
from typing import Optional
import pypdf
import docx

class ParserService:
    @staticmethod
    def extract_text(file_contents: bytes, filename: str) -> str:
        if filename.endswith(".pdf"):
            return ParserService._parse_pdf(file_contents)
        elif filename.endswith(".docx"):
            return ParserService._parse_docx(file_contents)
        elif filename.endswith(".txt"):
            return file_contents.decode("utf-8")
        else:
            raise ValueError("Unsupported file format")

    @staticmethod
    def _parse_pdf(file_contents: bytes) -> str:
        text = ""
        try:
            reader = pypdf.PdfReader(io.BytesIO(file_contents))
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
        except Exception as e:
            print(f"PDF parsing error: {e}")
        return text

    @staticmethod
    def _parse_docx(file_contents: bytes) -> str:
        text = ""
        try:
            doc = docx.Document(io.BytesIO(file_contents))
            for para in doc.paragraphs:
                text += para.text + "\n"
        except Exception as e:
            print(f"DOCX parsing error: {e}")
        return text