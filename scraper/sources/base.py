"""Clase base para todos los scrapers de fuentes oficiales."""
import re
import unicodedata
import requests
from abc import ABC, abstractmethod

JUNK_HEADINGS = {
    "main navigation", "news", "agenda", "footer links", "footer",
    "pasar al contenido principal", "volver atrás", "volver al inicio",
    "formulario de búsqueda de preguntas frecuentes",
    "configuración de cookies", "denegar todas", "aceptar todas",
    "documentación de cookies",
}


def norm(text):
    """Minúsculas y sin tildes, para comparar preguntas."""
    return "".join(
        c for c in unicodedata.normalize("NFD", text.lower())
        if not (0x300 <= ord(c) <= 0x36F)
    )


def clean_text(t):
    """Elimina restos de 'Leer más…' y compacta espacios."""
    t = re.sub(r"leer más sobre\s*['\"«].*", " ", t, flags=re.I)
    return re.sub(r"\s+", " ", t).strip()


def is_junk(question):
    """Detecta títulos basura (menús, fechas, textos cortos)."""
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
            "Mozilla/5.0 (compatible; FAQHubBot/1.0; "
            "+https://github.com/TU-USUARIO/faq-hub)"
        )
    }
    TIMEOUT = 30

    def fetch(self, url):
        try:
            resp = requests.get(url, headers=self.HEADERS, timeout=self.TIMEOUT)
            resp.raise_for_status()
            return resp.text
        except requests.RequestException as e:
            print(f"  ⚠️  Error al descargar {url}: {e}")
            return ""

    @abstractmethod
    def scrape(self):
        raise NotImplementedError
