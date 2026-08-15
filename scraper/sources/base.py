"""Clase base para todos los scrapers de fuentes oficiales."""
import requests
from abc import ABC, abstractmethod


class BaseScraper(ABC):
    SOURCE_ID = "base"
    BASE_URL = ""
    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (compatible; FAQHubBot/1.0; "
            "+https://github.com/TU-USUARIO/faq-hub)"
        )
    }
    TIMEOUT = 30

    def fetch(self, url: str) -> str:
        try:
            resp = requests.get(url, headers=self.HEADERS, timeout=self.TIMEOUT)
            resp.raise_for_status()
            return resp.text
        except requests.RequestException as e:
            print(f"  ⚠️  Error al descargar {url}: {e}")
            return ""

    @abstractmethod
    def scrape(self) -> list:
        raise NotImplementedError
