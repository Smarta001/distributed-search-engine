"""
parser.py
HTML Parser for the crawler.
 
Responsibilities:
- Extract page title
- Extract meta description
- Extract all links (resolved to absolute URLs)
- Extract headings (h1-h3) — optional, useful for indexing later
 
Returns a plain dict so it's easy to pass into database.py / rabbitmq.py
without needing a custom class.
"""
 
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
 
 
def parse_html(html, base_url):
    """
    Parse an HTML document and extract structured data.
 
    html:      raw HTML string (e.g. from downloader.DownloadResult.html)
    base_url:  the URL this HTML came from — used to resolve relative
               links (like "/about") into absolute URLs
 
    Returns a dict:
        {
            "title": str | None,
            "meta_description": str | None,
            "links": list[str],       # absolute URLs, deduped
            "headings": {
                "h1": list[str],
                "h2": list[str],
                "h3": list[str],
            },
        }
    """
    soup = BeautifulSoup(html, "html.parser")
 
    title = _extract_title(soup)
    meta_description = _extract_meta_description(soup)
    links = _extract_links(soup, base_url)
    headings = _extract_headings(soup)
 
    return {
        "title": title,
        "meta_description": meta_description,
        "links": links,
        "headings": headings,
    }
 
 
def _extract_title(soup):
    if soup.title and soup.title.string:
        return soup.title.string.strip()
    return None
 
 
def _extract_meta_description(soup):
    tag = soup.find("meta", attrs={"name": "description"})
    if tag and tag.get("content"):
        return tag["content"].strip()
 
    # Fall back to Open Graph description if a plain meta description
    # isn't present — many sites only set og:description.
    og_tag = soup.find("meta", attrs={"property": "og:description"})
    if og_tag and og_tag.get("content"):
        return og_tag["content"].strip()
 
    return None
 
 
def _extract_links(soup, base_url):
    links = []
    seen = set()
 
    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"].strip()
        if not href or href.startswith("#") or href.startswith("javascript:") or href.startswith("mailto:"):
            continue
 
        absolute_url = urljoin(base_url, href)
 
        # Only keep http/https links — skip ftp:, tel:, data:, etc.
        if urlparse(absolute_url).scheme not in ("http", "https"):
            continue
 
        if absolute_url not in seen:
            seen.add(absolute_url)
            links.append(absolute_url)
 
    return links
 
 
def _extract_headings(soup):
    headings = {"h1": [], "h2": [], "h3": []}
    for level in headings:
        for tag in soup.find_all(level):
            text = tag.get_text(strip=True)
            if text:
                headings[level].append(text)
    return headings
 
 
if __name__ == "__main__":
    # Quick manual test: python parser.py
    sample_html = """
    <html>
    <head>
        <title>  Example Domain  </title>
        <meta name="description" content="This domain is for use in examples.">
    </head>
    <body>
        <h1>Welcome</h1>
        <h2>Section One</h2>
        <p>Some text with a <a href="/about">relative link</a>
        and an <a href="https://other.com/page">absolute link</a>
        and a <a href="#top">fragment link</a> to skip.</p>
    </body>
    </html>
    """
 
    result = parse_html(sample_html, base_url="https://example.com")
    import json
    print(json.dumps(result, indent=2))