"""
downloader.py
HTML Downloader for the crawler.

Responsibilities:
- Download the HTML content of a given URL
- Handle timeouts gracefully
- Retry failed requests with backoff
- Return the HTTP status code alongside the content

Uses config.py for timeout, retry count, and User-Agent so all
crawler behavior stays centrally configurable.
"""

import time
import requests

import config


class DownloadResult:
    """
    Simple container for what a download attempt produced.

    url:            the URL that was requested
    status_code:    HTTP status code, or None if the request never
                     got a response (e.g. connection error / timeout)
    html:           response body text, or None on failure
    error:          error message if the download ultimately failed,
                     else None
    """

    def __init__(self, url, status_code=None, html=None, error=None):
        self.url = url
        self.status_code = status_code
        self.html = html
        self.error = error

    @property
    def success(self):
        return self.error is None and self.status_code is not None and 200 <= self.status_code < 300

    def __repr__(self):
        return (
            f"DownloadResult(url={self.url!r}, status_code={self.status_code}, "
            f"success={self.success}, error={self.error!r})"
        )


def download(url, timeout=None, max_retries=None, backoff_seconds=1.0):
    """
    Download a URL's HTML with retry-on-failure.

    timeout:          seconds to wait per attempt (defaults to config.REQUEST_TIMEOUT)
    max_retries:      total attempts before giving up (defaults to config.MAX_RETRIES)
    backoff_seconds:  base delay between retries, doubled each attempt (simple backoff)
    """
    timeout = timeout if timeout is not None else config.REQUEST_TIMEOUT
    max_retries = max_retries if max_retries is not None else config.MAX_RETRIES

    headers = {"User-Agent": config.USER_AGENT}

    last_error = None
    last_status = None

    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(url, headers=headers, timeout=timeout)
            last_status = response.status_code

            if response.ok:
                return DownloadResult(url, status_code=response.status_code, html=response.text)

            if 400 <= response.status_code < 500:
                return DownloadResult(
                    url,
                    status_code=response.status_code,
                    error=f"Client error {response.status_code}",
                )

            last_error = f"Server error {response.status_code}"

        except requests.exceptions.Timeout:
            last_error = f"Timeout after {timeout}s"
        except requests.exceptions.ConnectionError as e:
            last_error = f"Connection error: {e}"
        except requests.exceptions.RequestException as e:
            last_error = f"Request failed: {e}"

        if attempt < max_retries:
            time.sleep(backoff_seconds * attempt)

    return DownloadResult(url, status_code=last_status, error=last_error or "Unknown failure")


if __name__ == "__main__":
    test_urls = [
        "https://example.com",
        "https://example.com/this-page-does-not-exist",
    ]

    for u in test_urls:
        result = download(u)
        print(result)
        if result.success:
            print("  First 100 chars of HTML:", result.html[:100].replace("\n", " "))