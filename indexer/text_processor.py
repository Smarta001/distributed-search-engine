"""
Turns raw crawled HTML into the clean fields an IndexDocument needs:
title, body (plain text), keywords.

Pipeline: strip HTML -> spaCy tokenize -> drop stopwords/punctuation ->
lemmatize -> keep the body as readable text (for the ES `body` field, which
Elasticsearch itself will tokenize/stem again for BM25) while using the
lemmatized tokens only to derive `keywords`.

Note: spaCy does lemmatization, not stemming (e.g. "running" -> "run" via
dictionary lookup + POS, not suffix-stripping like Porter/Snowball). This is
usually a better match for BM25/ES's own analyzer than the crawler's original
stemming plan, so we lean on it here for keyword extraction. We deliberately
still feed ES the *original* cleaned body text (not lemmatized) for `body`,
and let Elasticsearch's own analyzer (see es_client.py mapping) do stemming
consistently at both index and query time.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

import spacy
from bs4 import BeautifulSoup

from shared.logger import get_logger

logger = get_logger(__name__)

_NLP = None  # lazy-loaded, spaCy model load is expensive


def _get_nlp():
    global _NLP
    if _NLP is None:
        logger.info("Loading spaCy model en_core_web_sm...")
        _NLP = spacy.load("en_core_web_sm", disable=["parser", "ner"])
    return _NLP


@dataclass
class ProcessedContent:
    title: str
    body: str
    keywords: list[str]
    lang: str | None


def strip_html(html: str) -> tuple[str, str]:
    """Returns (title, plain_text_body)."""
    soup = BeautifulSoup(html, "lxml")

    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else ""

    for tag in soup(["script", "style", "noscript", "nav", "footer", "header"]):
        tag.decompose()

    text = soup.get_text(separator=" ", strip=True)
    text = " ".join(text.split())  # collapse whitespace
    return title, text


def extract_keywords(body_text: str, top_n: int = 15) -> list[str]:
    """
    Lemmatize the body, drop stopwords/punctuation/short tokens, and return
    the most frequent lemmas as keywords. Good enough as a first pass —
    swap for TF-IDF or RAKE later if keyword quality matters more.
    """
    nlp = _get_nlp()
    doc = nlp(body_text[:200_000])  # guard against pathologically huge pages

    lemmas = [
        token.lemma_.lower()
        for token in doc
        if not token.is_stop
        and not token.is_punct
        and not token.is_space
        and token.is_alpha
        and len(token) > 2
    ]

    counts = Counter(lemmas)
    return [word for word, _ in counts.most_common(top_n)]


def process_html(html: str) -> ProcessedContent:
    title, body = strip_html(html)
    keywords = extract_keywords(body) if body else []

    lang = None
    if body:
        nlp = _get_nlp()
        lang = nlp.meta.get("lang")  # spaCy model's language, not per-doc detection

    return ProcessedContent(title=title, body=body, keywords=keywords, lang=lang)
