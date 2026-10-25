import logging
from copy import deepcopy
from urllib.parse import urldefrag, urljoin, urlsplit

from bs4 import BeautifulSoup, Tag

logger = logging.getLogger(__name__)


class HTMLParser:
    def __init__(self):
        self.backend = "lxml"

    def extract_metadata(self, soup: BeautifulSoup) -> dict:
        title = soup.find("title")
        metadata = {
            "title": title.get_text().strip() if title is not None else "",
            "description": "",
            "keywords": "",
        }
        for name in ("description", "keywords"):
            tag = soup.find("meta", attrs={"name": name})
            if tag is not None:
                metadata[name] = tag.get("content", "").strip()
        return metadata

    def extract_text(
            self,
            soup: BeautifulSoup,
            selector: str | None = None,
    ) -> str:
        if selector is None:
            element = soup.body if soup.body is not None else soup
        else:
            element = soup.select_one(selector)

        if element is None or element.name in ("script", "style", "noscript"):
            return ""

        fragment = deepcopy(element)
        for tag in fragment.find_all(["script", "style", "noscript"]):
            tag.decompose()

        text = fragment.get_text(separator=" ", strip=True)
        return " ".join(text.split())

    def extract_links(self, soup: BeautifulSoup, base_url: str) -> list[str]:
        links = []
        seen = set()

        for tag in soup.find_all("a", href=True):
            href = tag["href"].strip()
            if not href or href.startswith("#"):
                continue
            if any(char.isspace() for char in href):
                continue

            try:
                absolute_url = urljoin(base_url, href)
                if any(char.isspace() for char in absolute_url):
                    continue
                parsed = urlsplit(absolute_url)
                if parsed.scheme not in ("http", "https") or not parsed.hostname:
                    continue
                _ = parsed.port
                absolute_url, _ = urldefrag(absolute_url)
            except ValueError:
                continue

            if absolute_url not in seen:
                seen.add(absolute_url)
                links.append(absolute_url)

        return links

    @staticmethod
    def _extract_element_text(
            element: Tag,
            excluded_tags: tuple[str, ...] = (),
    ) -> str:
        fragment = deepcopy(element)
        for tag in fragment.find_all(("script", "style", "noscript") + excluded_tags):
            tag.extract()
        return " ".join(fragment.get_text(separator=" ", strip=True).split())

    def extract_images(self, soup: BeautifulSoup) -> list[dict]:
        return [
            {
                "src": image.get("src", "").strip(),
                "alt": image.get("alt", "").strip(),
            }
            for image in soup.find_all("img")
        ]

    def extract_headings(self, soup: BeautifulSoup) -> list[dict]:
        return [
            {
                "level": int(heading.name[1]),
                "text": self._extract_element_text(heading),
            }
            for heading in soup.find_all(["h1", "h2", "h3"])
        ]

    def extract_tables(self, soup: BeautifulSoup) -> list[list[list[str]]]:
        tables = []
        for table in soup.find_all("table"):
            rows = []
            for row in table.find_all("tr"):
                if row.find_parent("table") is not table:
                    continue
                cells = [
                    self._extract_element_text(cell, ("table",))
                    for cell in row.find_all(["th", "td"])
                    if cell.find_parent("table") is table
                       and cell.find_parent("tr") is row
                ]
                rows.append(cells)
            tables.append(rows)
        return tables

    def extract_lists(self, soup: BeautifulSoup) -> list[dict]:
        return [
            {
                "type": element.name,
                "items": [
                    self._extract_element_text(item, ("ul", "ol"))
                    for item in element.find_all("li", recursive=False)
                ],
            }
            for element in soup.find_all(["ul", "ol"])
        ]

    async def parse_html(self, html: str, url: str) -> dict:
        result = {
            "url": url,
            "title": "",
            "text": "",
            "links": [],
            "metadata": {"title": "", "description": "", "keywords": ""},
            "images": [],
            "headings": [],
            "tables": [],
            "lists": [],
        }

        try:
            soup = BeautifulSoup(html, self.backend)
        except Exception as error:
            logger.warning(
                "Parsing failed | URL: %s | Stage: BeautifulSoup | Type: %s | Reason: %s",
                url, type(error).__name__, error,
            )
            return result

        stages = (
            ("metadata", self.extract_metadata, (soup,)),
            ("text", self.extract_text, (soup,)),
            ("links", self.extract_links, (soup, url)),
            ("images", self.extract_images, (soup,)),
            ("headings", self.extract_headings, (soup,)),
            ("tables", self.extract_tables, (soup,)),
            ("lists", self.extract_lists, (soup,)),
        )
        for field, extractor, args in stages:
            try:
                value = extractor(*args)
                if field == "metadata":
                    title = value["title"]
                    result["title"] = title
                result[field] = value
            except Exception as error:
                logger.warning(
                    "Parsing failed | URL: %s | Stage: %s | Type: %s | Reason: %s",
                    url, field, type(error).__name__, error,
                )

        return result
