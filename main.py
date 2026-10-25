import asyncio
import json
import logging
import time

from src.crawler import AsyncCrawler

URLS = [
    "https://example.com",
    "https://www.python.org",
    "https://httpbin.org/html",
]


async def main():
    crawler = AsyncCrawler(max_concurrent=3)
    start = time.perf_counter()

    try:
        results = await asyncio.gather(
            *(crawler.fetch_and_parse(url) for url in URLS)
        )
    finally:
        await crawler.close()

    elapsed = time.perf_counter() - start

    summaries = [
        {
            "url": page["url"],
            "title": page["title"],
            "text_length": len(page["text"]),
            "links_count": len(page["links"]),
            "links": page["links"],
            "images_count": len(page["images"]),
            "headings": page["headings"],
        }
        for page in results
    ]
    print(json.dumps(summaries, ensure_ascii=False, indent=2))
    print(f"\nВремя выполнения: {elapsed:.2f} сек.")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s"
    )

    asyncio.run(main())
