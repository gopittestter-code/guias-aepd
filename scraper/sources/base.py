"""Clase base para todos los scrapers de fuentes oficiales.
Cadena de descarga anti-bloqueo:
  1) requests directo
  2) proxies de lectura gratuitos (otros servidores)
  3) navegador headless real (Playwright)
"""
import re
import time
import unicodedata
import urllib.parse

import requests
from abc import ABC, abstractmethod

JUNK_HEADINGS = {
    "main navigation", "news", "agenda", "footer links", "footer",
    "pasar al contenido principal", "volver atrás", "volver al inicio",
    "formulario de búsqueda de preguntas frecuentes",
    "configuración de cookies", "denegar todas", "aceptar todas",
    "documentación de cookies", "buscar",
}

PROXY_TEMPLATES = [
    "https://api.allorigins.win/raw?url={}",
    "https://corsproxy.io/?url={}",
]

_PW = None
_BROWSER = None
_PROXY_LOGGED = set()


def _get_browser():
    global _PW, _BROWSER
    if _BROWSER is None:
        from playwright.sync_api import sync_playwright
        _PW = sync_playwright().start()
        _BROWSER = _PW.chromium.launch(headless=True)
    return _BROWSER


def close_browser():
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

    # ---------- 1) requests ----------
    def _fetch_requests(self, url):
        try:
            resp = requests.get(url, headers=self.HEADERS, timeout=self.TIMEOUT)
            if resp.status_code == 200 and len(resp.text) > 200:
                return resp.text
        except requests.RequestException:
            pass
        return ""

    # ---------- 2) proxies gratuitos ----------
    def _fetch_proxy(self, url):
        enc = urllib.parse.quote(url, safe="")
        for tmpl in PROXY_TEMPLATES:
            try:
                resp = requests.get(tmpl.format(enc), headers=self.HEADERS, timeout=self.TIMEOUT)
                if resp.status_code == 200 and len(resp.text) > 500:
                    host = urllib.parse.urlparse(url).netloc
                    if host not in _PROXY_LOGGED:
                        print(f"  🔀 {host} descargado vía proxy")
                        _PROXY_LOGGED.add(host)
                    return resp.text
            except requests.RequestException:
                continue
        return ""

    # ---------- 3) navegador headless ----------
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

    def fetch(self, url):
        """Prueba requests → proxy → navegador, en ese orden."""
        return (
            self._fetch_requests(url)
            or self._fetch_proxy(url)
            or self._fetch_browser(url)
        )

    def fetch_rendered(self, url):
        """Para páginas pintadas con JavaScript: navegador directo, con respaldo."""
        return self._fetch_browser(url) or self._fetch_proxy(url) or self._fetch_requests(url)

    @abstractmethod
    def scrape(self):
        raise NotImplementedError
