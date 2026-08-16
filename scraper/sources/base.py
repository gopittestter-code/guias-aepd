"""Clase base para todos los scrapers de fuentes oficiales.
Usa requests y, si el sitio bloquea (401/403), cae a un navegador
headless real (Playwright) que supera los filtros anti-bot."""
import re
import time
import unicodedata

import requests
from abc import ABC, abstractmethod

JUNK_HEADINGS = {
    "main navigation", "news", "agenda", "footer links", "footer",
    "pasar al contenido principal", "volver atrás", "volver al inicio",
    "formulario de búsqueda de preguntas frecuentes",
    "configuración de cookies", "denegar todas", "aceptar todas",
    "documentación de cookies", "buscar",
}

_PW = None
_BROWSER = None


def _get_browser():
    """Lanza un único navegador headless compartido."""
    global _PW, _BROWSER
    if _BROWSER is None:
        from playwright.sync_api import sync_playwright
        _PW = sync_playwright().start()
        _BROWSER = _PW.chromium.launch(headless=True)
    return _BROWSER


def close_browser():
    """Cierra el navegador al terminar."""
    global _PW, _BROWSER
    try:
        if _BROWSER is not None:
            _BROWSER.close()
        if _PW is not None:
            _PW.stop()
    except Exception:
        pass
    _BROWSER = None
    _PW = None


def norm(text):
    return "".join(
        c for c in unicodedata.normalize("NFD", text.lower())
        if not (0x300 <= ord(c) <= 0x36F)
    )


def clean_text(t):
    t = re.sub(r"leer más sobre\s*['\"«].*", " ", t, flags=re.I)
    return re.sub(r"\s+", " ", t).strip()


def is_junk(question):
    q = question.strip()
    return (
        len(q) < 6
        or q.lower() in JUNK_HEADINGS
        or bool(re.match(r"^\d{1,2}\s+[A-Za-zÁ-ú]+\s+\d{4}", q))
    )


class BaseScraper(ABC):
    SOURCE_ID = "base"
    BASE_URL = ""
    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
        "Referer": "https://www.google.com/",
    }
    TIMEOUT = 30

    def fetch(self, url, retries=2):
        """Descarga con requests; si bloquean (401/403), usa navegador."""
        for attempt in range(retries + 1):
            try:
                resp = requests.get(url, headers=self.HEADERS, timeout=self.TIMEOUT)
                if resp.status_code in (401, 403):
                    break  # bloqueado → ir directo al navegador
                resp.raise_for_status()
                return resp.text
            except requests.RequestException:
                if attempt < retries:
                    time.sleep(2 * (attempt + 1))
        return self._fetch_browser(url)

    def _fetch_browser(self, url):
        try:
            page = _get_browser().new_page()
            page.goto(url, timeout=60000, wait_until="domcontentloaded")
            page.wait_for_timeout(1500)
            html = page.content()
            page.close()
            return html
        except Exception as e:
            print(f"  ⚠️  El navegador también falló ({url}): {e}")
            return ""

    def fetch_rendered(self, url):
        """Para páginas pintadas con JavaScript: navegador directo."""
        return self._fetch_browser(url) or self.fetch(url)

    @abstractmethod
    def scrape(self):
        raise NotImplementedError
