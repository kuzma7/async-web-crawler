import asyncio
import logging
import time

import aiohttp

from src.html_parser import HTMLParser

logger = logging.getLogger(__name__)


class AsyncCrawler:

    def __init__(self, max_concurrent: int = 10):
        if max_concurrent < 1:
            raise ValueError("max_concurrent должен быть больше 0")

        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.max_concurrent = max_concurrent
        self.timeout = aiohttp.ClientTimeout(
            total=15,
            connect=5,
            sock_read=10
        )
        self.session = None
        self.parser = HTMLParser()

    async def start(self):
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                timeout=self.timeout,
                connector=aiohttp.TCPConnector(
                    limit=self.max_concurrent
                )
            )

    async def fetch_url(self, url: str) -> str:
        if self.session is None or self.session.closed:
            await self.start()
        try:
            async with self.semaphore:
                logger.info("Начинаем загрузку %s", url)
                start = time.perf_counter()

                async with self.session.get(url) as response:
                    response.raise_for_status()
                    html = await response.text()
                    elapsed = time.perf_counter() - start
                    logger.info(
                        "Успешно загружен %s за %.2f сек.",
                        url,
                        elapsed
                    )

                    return html
        except aiohttp.ClientResponseError as error:
            logger.error(
                "HTTP ошибка | URL: %s | Тип: %s | Статус: %s",
                url,
                type(error).__name__,
                error.status
            )
            return ""

        except asyncio.TimeoutError as error:
            logger.error(
                "Таймаут | URL: %s | Тип: %s",
                url,
                type(error).__name__
            )
            return ""

        except aiohttp.ClientError as error:
            logger.error(
                "Сетевая ошибка | URL: %s | Тип: %s | Причина: %s",
                url,
                type(error).__name__,
                error
            )
            return ""

    async def fetch_urls(
            self,
            urls: list[str]
    ) -> dict[str, str]:

        if not urls:
            return {}
        await self.start()

        logger.info("Запускаем загрузку %d URL", len(urls))
        responses = await asyncio.gather(
            *(self.fetch_url(url) for url in urls)
        )
        results = dict(zip(urls, responses))
        logger.info("Загрузка завершена")
        return results

    async def fetch_and_parse(self, url: str) -> dict:
        html = await self.fetch_url(url)
        return await self.parser.parse_html(html, url)

    async def close(self) -> None:
        if self.session is not None and not self.session.closed:
            await self.session.close()
            self.session = None

            logger.info("HTTP-сессия закрыта")
