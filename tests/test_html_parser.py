import logging

import pytest
from bs4 import BeautifulSoup

from src.html_parser import HTMLParser


@pytest.mark.asyncio
async def test_parse_valid_html():
    html = '''
    <html><head><title> Example </title>
    <meta name="description" content=" A page ">
    <meta name="keywords" content="python, asyncio"></head>
    <body><h1>Hello</h1><p>A <b>test</b> page.</p>
    <script>hidden</script><style>hidden</style><noscript>hidden</noscript>
    <img src=" /logo.png " alt=" Logo "><img src="/photo.png">
    <table><tr><th>Name</th><th>Age</th></tr>
    <tr><td>Anna</td><td>25</td></tr></table>
    <ul><li>First</li><li>Second</li></ul></body></html>
    '''
    result = await HTMLParser().parse_html(html, "https://example.com")
    assert result == {
        "url": "https://example.com",
        "title": "Example",
        "text": "Hello A test page. Name Age Anna 25 First Second",
        "metadata": {
            "title": "Example", "description": "A page", "keywords": "python, asyncio",
        },
        "links": [],
        "images": [{"src": "/logo.png", "alt": "Logo"}, {"src": "/photo.png", "alt": ""}],
        "headings": [{"level": 1, "text": "Hello"}],
        "tables": [[["Name", "Age"], ["Anna", "25"]]],
        "lists": [{"type": "ul", "items": ["First", "Second"]}],
    }


@pytest.mark.asyncio
async def test_parse_broken_html():
    result = await HTMLParser().parse_html(
        '<html><head><title>Broken</title></head><body><h1>Hello</h1>'
        '<p>Unclosed <b>text</b><a href="/next">Next',
        "https://example.com/page",
    )
    assert result["title"] == "Broken"
    assert result["text"] == "Hello Unclosed text Next"
    assert result["headings"] == [{"level": 1, "text": "Hello"}]
    assert result["links"] == ["https://example.com/next"]


def test_extract_links():
    soup = BeautifulSoup('''
        <a href="https://other.example/page?q=1#part">External</a>
        <a href=" /next ">Root</a><a href="../next">Duplicate</a>
        <a href="child">Relative</a><a href="//cdn.example/file">CDN</a>
        <a href="/next#part">Duplicate fragment</a><a href="#part">Anchor</a>
        <a href="mailto:user@example.com">Mail</a><a href="javascript:alert(1)">JS</a>
        <a href="https://example.com:bad">Bad port</a>
        <a href="https://example.com:99999">Invalid port range</a>
        <a href="http://[broken">Bad host</a><a href="https://exa mple.com">Space</a>
        <a href="">Empty</a><a>Missing</a><a href="/last">Last</a>
    ''', "lxml")
    original = str(soup)
    assert HTMLParser().extract_links(soup, "https://example.com/docs/page") == [
        "https://other.example/page?q=1",
        "https://example.com/next",
        "https://example.com/docs/child",
        "https://cdn.example/file",
        "https://example.com/last",
    ]
    assert str(soup) == original


@pytest.mark.asyncio
async def test_parse_empty_html():
    assert await HTMLParser().parse_html("", "https://example.com") == {
        "url": "https://example.com", "title": "", "text": "", "links": [],
        "metadata": {"title": "", "description": "", "keywords": ""},
        "images": [], "headings": [], "tables": [], "lists": [],
    }


@pytest.mark.asyncio
async def test_parse_preserves_partial_results(monkeypatch, caplog):
    parser = HTMLParser()

    def fail_tables(soup):
        raise ValueError("Invalid table")

    monkeypatch.setattr(parser, "extract_tables", fail_tables)
    url = "https://example.com/page"
    with caplog.at_level(logging.WARNING, logger="src.html_parser"):
        result = await parser.parse_html(
            '<title>Example</title><body><h1>Hello</h1><a href="/next">Next</a>'
            '<ul><li>Item</li></ul></body>', url,
        )
    assert result["tables"] == []
    assert result["title"] == "Example"
    assert result["text"] == "Hello Next Item"
    assert result["links"] == ["https://example.com/next"]
    assert result["headings"] == [{"level": 1, "text": "Hello"}]
    assert result["lists"] == [{"type": "ul", "items": ["Item"]}]
    assert all(part in caplog.text for part in (url, "tables", "ValueError", "Invalid table"))
