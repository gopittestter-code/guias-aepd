"""Scraper de las guías oficiales del CCN-CERT (lee la tabla de documentos)."""
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from .base import BaseScraper, clean_text, is_junk

MONTHS = {
    "ene":1,"feb":2,"mar":3,"abr":4,"may":5,"jun":6,
    "jul":7,"ago":8,"sep":9,"oct":10,"nov":11,"dic":12,
    "enero":1,"febrero":2,"marzo":3,"abril":4,"mayo":5,"junio":6,
    "julio":7,"agosto":8,"septiembre":9,"octubre":10,"noviembre":11,"diciembre":12,
}

TOPIC_TO_CAT = {
    "procedimiento": "ciberseguridad_conceptos",
    "empleo seguro": "ciberseguridad_conceptos",
    "catálogo": "ciberseguridad_conceptos",
    "perfilado": "ciberseguridad_conceptos",
    "linux": "ciberseguridad_conceptos",
    "windows": "ciberseguridad_conceptos",
    "incidente": "incidentes",
    "ransomware": "ransomware",
    "cript": "ciberseguridad_conceptos",
    "seguridad": "ciberseguridad_conceptos",
}


class CCNCertGuidesScraper(BaseScraper):
    SOURCE_ID = "ccn_cert_guides"
    BASE_URL = "https://www.ccn-cert.cni.es/es/guias.html"

    def scrape(self):
        html = self.fetch(self.BASE_URL)
        if not html:
            return []

        soup = BeautifulSoup(html, "lxml")
        guides = []
        seen = set()

        # La página es una tabla: cada fila (<tr>) contiene el enlace del documento.
        # Si no hubiera <tr>, probamos bloques genéricos.
        rows = soup.select("tr") or soup.select("article, li, .row, .item, .views-row")

        for row in rows:
            # Busca el enlace cuyo texto sea un código CCN-STIC / CCN
            link = None
            for a in row.select("a[href]"):
                t = clean_text(a.get_text(" ", strip=True))
                if re.search(r"\bCCN[-\s]?STIC\b", t, re.I) or t.upper().startswith("CCN"):
                    link = a
                    break
            if not link:
                continue

            url = urljoin(self.BASE_URL, link.get("href", ""))
            if url in seen:
                continue
            seen.add(url)

            title = clean_text(link.get_text(" ", strip=True))
            if not title or is_junk(title):
                continue

            row_text = row.get_text(" ")

            # Categoría (columna "Categoría:")
            cat_m = re.search(r"Categoría:\s*([^|]{0,80})", row_text, re.I)
            topic = clean_text(cat_m.group(1)) if cat_m else ""

            # Fecha de publicación ("Publicado desde: Jul 2025")
            date = None
            d_m = re.search(r"Publicado desde:\s*([A-Za-zÁ-ú]{3,})\s+(\d{4})", row_text, re.I)
            if d_m:
                key = d_m.group(1).lower()
                mon = MONTHS.get(key) or MONTHS.get(key[:3])
                if mon:
                    date = f"{d_m.group(2)}-{mon:02d}-01"

            guides.append({
                "id": f"guide_ccn_{len(guides)+1:03d}",
                "source": self.SOURCE_ID,
                "type": "guide",
                "category": self._topic_to_cat(title + " " + topic),
                "topic": topic or self._code(title),
                "title": title,
                "summary": "",
                "published_date": date,
                "tags": ["CCN-CERT", "guía", "CCN-STIC", "ciberseguridad"],
                "url": url,                 # 🔧 URL real de cada guía, no la general
                "url_original": url,
            })

        print(f"  ✅ CCN-CERT Guías: {len(guides)} documentos")
        return guides

    def _code(self, title):
        m = re.match(r"^(CCN[-\s]?STIC[-\s]?[\w./-]+)", title, re.I)
        return m.group(1).strip() if m else title[:60]

    def _topic_to_cat(self, text):
        tl = text.lower()
        for k, v in TOPIC_TO_CAT.items():
            if k in tl:
                return v
        return "ciberseguridad_conceptos"
