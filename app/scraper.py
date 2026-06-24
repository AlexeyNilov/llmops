# scraper.py

import asyncio
import re

import httpx
from bs4 import BeautifulSoup
from loguru import logger


def extract_urls(text: str) -> list[str]:
    url_pattern = r"(?P<url>https?:\/\/[^\s]+)"
    urls = re.findall(url_pattern, text)
    return urls


def parse_inner_text(html_string: str) -> str:
    soup = BeautifulSoup(html_string, "lxml")
    if content := soup.find("div", id="bodyContent"):
        return content.get_text()
    logger.warning("Could not parse the HTML content")
    return ""


async def fetch(client: httpx.AsyncClient, url: str) -> str:
    response = await client.get(url)
    return parse_inner_text(response.text)


async def fetch_all(urls: list[str]) -> str:
    async with httpx.AsyncClient() as client:
        results = await asyncio.gather(
            *[fetch(client, url) for url in urls], return_exceptions=True
        )
    success_results = [result for result in results if isinstance(result, str)]
    if len(results) != len(success_results):
        logger.warning("Some URLs could not be fetched")
    return " ".join(success_results)


async def get_urls_content(prompt: str) -> str:
    urls = extract_urls(prompt)
    if urls:
        try:
            urls_content = await fetch_all(urls)
            return urls_content
        except Exception as e:
            logger.warning(f"Failed to fetch one or several URls - Error: {e}")
    return ""