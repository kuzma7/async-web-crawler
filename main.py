
import asyncio
import logging
import time

from src.crawler import AsyncCrawler


async def main():
    urls = [
        "https://example.com",
        "https://httpbin.org/status/404",
        "https://httpbin.org/delay/20",
    ]

    crawler = AsyncCrawler(max_concurrent=3)
    await crawler.start()
    start = time.perf_counter()

    try:
        results = await crawler.fetch_urls(urls)

        for url, html in results.items():
            status = "OK" if html else "ERROR"
            print(f"{status} | {url} | {len(html)} символов")

    finally:
        await crawler.close()

    elapsed = time.perf_counter() - start

    print(f"\nОбщее время: {elapsed:.2f} сек.")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s"
    )

    asyncio.run(main())
