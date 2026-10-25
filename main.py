import asyncio
import logging
import time

from src.crawler import AsyncCrawler

URLS = [
    "https://example.com",
    "https://www.python.org",
    "https://httpbin.org/get",
    "https://httpbin.org/delay/1",
    "https://httpbin.org/status/404",
    "https://httpbin.org/headers",
]


async def run_crawler(max_concurrent: int) -> float:
    crawler = AsyncCrawler(max_concurrent=max_concurrent)
    start = time.perf_counter()

    try:
        results = await crawler.fetch_urls(URLS)

        for url, html in results.items():
            status = "OK" if html else "ERROR"
            print(f"{status} | {url}")

    finally:
        await crawler.close()

    elapsed = time.perf_counter() - start

    print(f"Время выполнения: {elapsed:.2f} сек.")
    return elapsed


async def main():
    print("=== Последовательная загрузка ===")
    sequential = await run_crawler(max_concurrent=1)

    print("\n=== Конкурентная загрузка ===")
    concurrent = await run_crawler(max_concurrent=5)

    if concurrent > 0:
        print(
            f"\nУскорение: {sequential / concurrent:.2f}x"
        )


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s"
    )

    asyncio.run(main())
