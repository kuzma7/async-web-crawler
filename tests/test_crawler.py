import asyncio
from contextlib import asynccontextmanager

import aiohttp
import pytest
from aiohttp import web

from src.crawler import AsyncCrawler


@asynccontextmanager
async def local_server():
    async def handler(request):
        path = request.path

        if path == "/not-found":
            return web.Response(status=404, text="Not found")

        if path == "/page":
            return web.Response(
                text='<title>Example</title><body><h1>Hello</h1>'
                     '<a href="/next">Next</a></body>',
                content_type="text/html",
            )

        if path == "/slow":
            await asyncio.sleep(0.5)

        return web.Response(text="<html>Test page</html>")

    app = web.Application()
    app.router.add_get("/{path:.*}", handler)

    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()

    port = site._server.sockets[0].getsockname()[1]

    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        await runner.cleanup()


@pytest.mark.asyncio
async def test_fetch_and_parse_without_start():
    async with local_server() as base_url:
        crawler = AsyncCrawler()
        try:
            result = await crawler.fetch_and_parse(f"{base_url}/page")
            assert result["url"] == f"{base_url}/page"
            assert result["title"] == "Example"
            assert result["text"] == "Hello Next"
            assert result["links"] == [f"{base_url}/next"]
            session = crawler.session
            assert session is not None and not session.closed
        finally:
            await crawler.close()
        assert session.closed


@pytest.mark.asyncio
async def test_fetch_urls_without_start():
    async with local_server() as base_url:
        crawler = AsyncCrawler(max_concurrent=5)
        urls = [base_url, f"{base_url}/second"]

        try:
            results = await crawler.fetch_urls(urls)

            assert results == {
                url: "<html>Test page</html>" for url in urls
            }
            session = crawler.session
            assert session is not None
            assert not session.closed

            assert await crawler.fetch_urls(urls) == results
            assert crawler.session is session
        finally:
            await crawler.close()

        assert session.closed
        assert crawler.session is None
        await crawler.close()


@pytest.mark.asyncio
async def test_fetch_valid_url():
    async with local_server() as base_url:
        crawler = AsyncCrawler()
        await crawler.start()

        try:
            html = await crawler.fetch_url(base_url)

            assert "<html>Test page</html>" == html
        finally:
            await crawler.close()


@pytest.mark.asyncio
async def test_fetch_404():
    async with local_server() as base_url:
        crawler = AsyncCrawler()
        await crawler.start()

        try:
            result = await crawler.fetch_url(
                f"{base_url}/not-found"
            )

            assert result == ""
        finally:
            await crawler.close()


@pytest.mark.asyncio
async def test_fetch_timeout():
    async with local_server() as base_url:
        crawler = AsyncCrawler()

        crawler.timeout = aiohttp.ClientTimeout(
            total=0.05
        )

        await crawler.start()

        try:
            result = await crawler.fetch_url(
                f"{base_url}/slow"
            )

            assert result == ""
        finally:
            await crawler.close()
