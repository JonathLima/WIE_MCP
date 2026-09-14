"""Tests for extract_readability_content (trafilatura-backed)."""
from __future__ import annotations

import pytest

from src.utils.readability import extract_readability_content


def _make_html(lang: str, title: str, author: str, content_paragraphs: list[str]) -> str:
    paragraphs = "".join(f"<p>{p}</p>" for p in content_paragraphs)
    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
  <meta charset="UTF-8">
  <title>{title}</title>
  <meta name="author" content="{author}">
</head>
<body>
  <article>
    <h1>{title}</h1>
    {paragraphs}
  </article>
</body>
</html>"""


EN_PARAGRAPHS = [
    "Artificial intelligence is transforming industries worldwide. Companies are investing billions.",
    "Machine learning algorithms are now able to recognize images, translate languages, and generate text.",
    "The future of AI includes autonomous vehicles, personalized medicine, and advanced robotics.",
]

PT_PARAGRAPHS = [
    "A inteligencia artificial esta transformando industrias em todo o mundo. Empresas investem bilhoes.",
    "Algoritmos de aprendizado de maquina reconhecem imagens, traduzem linguas e geram texto automaticamente.",
    "O futuro da IA inclui veiculos autonomos, medicina personalizada e robotica avancada no Brasil.",
]

ES_PARAGRAPHS = [
    "La inteligencia artificial esta transformando industrias en todo el mundo. Empresas invierten millones.",
    "Los algoritmos de aprendizaje automatico reconocen imagenes, traducen idiomas y generan texto.",
    "El futuro de la IA incluye vehiculos autonomos, medicina personalizada y robotica avanzada en Europa.",
]


class TestExtractReadabilityContent:
    def test_en_content_not_empty(self):
        html = _make_html("en", "AI Article", "John Doe", EN_PARAGRAPHS)
        result = extract_readability_content(html, source_url="https://example.com/ai")
        assert result["content"], "content should not be empty for EN fixture"
        assert len(result["content"]) > 50

    def test_pt_content_not_empty(self):
        html = _make_html("pt", "Artigo IA", "Maria Silva", PT_PARAGRAPHS)
        result = extract_readability_content(html, source_url="https://example.com.br/ia")
        assert result["content"], "content should not be empty for PT fixture"
        assert len(result["content"]) > 50

    def test_es_content_not_empty(self):
        html = _make_html("es", "Articulo IA", "Carlos Lopez", ES_PARAGRAPHS)
        result = extract_readability_content(html, source_url="https://example.es/ia")
        assert result["content"], "content should not be empty for ES fixture"
        assert len(result["content"]) > 50

    def test_en_content_language(self):
        html = _make_html("en", "AI Article", "John", EN_PARAGRAPHS)
        result = extract_readability_content(html)
        assert result["content_language"] == "en"

    def test_pt_content_language(self):
        html = _make_html("pt-BR", "Artigo IA", "Maria", PT_PARAGRAPHS)
        result = extract_readability_content(html)
        assert result["content_language"] == "pt"

    def test_es_content_language(self):
        html = _make_html("es", "Articulo IA", "Carlos", ES_PARAGRAPHS)
        result = extract_readability_content(html)
        assert result["content_language"] == "es"

    def test_title_extracted(self):
        html = _make_html("en", "My Test Title", "Author", EN_PARAGRAPHS)
        result = extract_readability_content(html)
        assert "My Test Title" in result["title"]

    def test_return_keys_present(self):
        html = _make_html("en", "Test", "Author", EN_PARAGRAPHS)
        result = extract_readability_content(html)
        expected_keys = {"title", "description", "content", "headings", "was_truncated",
                         "content_language", "author", "published_date"}
        assert expected_keys.issubset(result.keys())

    def test_truncation(self):
        html = _make_html("en", "Long Article", "Author", EN_PARAGRAPHS * 20)
        result = extract_readability_content(html, max_length=200)
        assert result["was_truncated"] is True
        assert len(result["content"]) <= 300
