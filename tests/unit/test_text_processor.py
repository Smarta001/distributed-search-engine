"""
Unit tests for indexer/text_processor.py.

These load a real spaCy model, so the first test run will be slower
(model load) — subsequent tests reuse the cached `_NLP` instance.
"""

from indexer.text_processor import extract_keywords, process_html, strip_html


class TestStripHtml:
    def test_extracts_title_and_text(self):
        html = "<html><head><title>My Page</title></head><body><p>Hello world</p></body></html>"
        title, body = strip_html(html)
        assert title == "My Page"
        assert "Hello world" in body

    def test_removes_script_and_nav_content(self):
        html = """
        <html><head><title>T</title></head>
        <body>
            <nav>Skip this nav link</nav>
            <script>var shouldNotAppear = 1;</script>
            <p>Real content here</p>
        </body></html>
        """
        _, body = strip_html(html)
        assert "Real content here" in body
        assert "shouldNotAppear" not in body
        assert "Skip this nav link" not in body

    def test_missing_title_returns_empty_string(self):
        html = "<html><body><p>No title here</p></body></html>"
        title, _ = strip_html(html)
        assert title == ""

    def test_collapses_whitespace(self):
        html = "<html><body><p>Too    many\n\n  spaces</p></body></html>"
        _, body = strip_html(html)
        assert "  " not in body


class TestExtractKeywords:
    def test_drops_stopwords_and_short_tokens(self):
        text = "The quick brown fox jumps over the lazy dog repeatedly and quickly"
        keywords = extract_keywords(text, top_n=10)
        assert "the" not in keywords
        assert "and" not in keywords
        assert "over" not in keywords  # stopword
        assert any(k in keywords for k in ("quick", "fox", "jump", "lazy", "dog"))

    def test_empty_text_returns_empty_list(self):
        assert extract_keywords("") == []

    def test_lemmatizes_not_stems(self):
        # "running" should lemmatize to "run" (dictionary form), not a
        # truncated stem like "runn" — this is the key behavioral
        # difference from Porter/Snowball stemming.
        keywords = extract_keywords("Running dogs are running quickly through running fields")
        assert "run" in keywords


class TestProcessHtml:
    def test_full_pipeline_produces_all_fields(self):
        html = (
            "<html><head><title>Distributed Systems</title></head>"
            "<body><p>Distributed search engines crawl and index web pages efficiently.</p></body></html>"
        )
        result = process_html(html)
        assert result.title == "Distributed Systems"
        assert "Distributed search engines" in result.body
        assert len(result.keywords) > 0
        assert result.lang == "en"

    def test_empty_html_does_not_crash(self):
        result = process_html("<html><body></body></html>")
        assert result.title == ""
        assert result.keywords == []
