"""Scraper de las guías oficiales del CCN-CERT (tabla renderizada con JS)."""
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from .base import BaseScraper, clean_text, is_junk

MONTHS = {
    "ene":1,"feb":2,"mar":3,"abr":4,"may":5,"jun":6,
    "jul":7,"ago":8,"sep":9,"oct":10,"nov":11,"dic":12,
}

TOPIC_TO_CAT = {
    "procedimiento": "ciberseguridad_conceptos",
    "empleo seguro": "ciberseguridad_conceptos",
    "catálogo": "ciberseguridad_conceptos",
    "perfilado": "ciberseguridad_conceptos",
    "incidente": "incidentes",
    "ransomware": "ransomware",
    "cript": "ciberseguridad_conceptos",
    "seguridad": "ciberseguridad_conceptos",
}


class CCNCertGuidesScraper(BaseScraper):
    SOURCE_ID = "ccn_cert_guides"
    BASE_URL = "https://www.ccn-cert.cni.es/es/guias.html"

    def scrape(self):
        html = self.fetch_rendered(self.BASE_URL)
        if not html:
            return []

        soup = BeautifulSoup(html, "lxml")
        guides = []
        seen = set()

        rows = soup.select("tr") or soup.select("article, li, .row, .item, .views-row")

        for row in rows:
            row_text = row.get_text(" ")
            m = re.search(r"CCN[-\s]?STIC", row_text, re.I)
            if not m:
                continue

            # Título: desde "CCN-STIC" hasta "Categoría" (o 160 caracteres)
            start = m.start()
            end = row_text.find("Categoría", start)
            title = clean_text(row_text[start: end if end != -1 else start + 160])
            if not title or is_junk(title):
                continue

            # Enlace: primero cualquier PDF; si no, cualquier ancla útil
            link = None
            for a in row.select("a[href]"):
                if ".pdf" in a["href"].lower():
                    link = urljoin(self.BASE_URL, a["href"])
                    break
            if not link:
                for a in row.select("a[href]"):
                    href = a["href"]
                    abs_url = urljoin(self.BASE_URL, href)
                    if (href and not href.startswith(("#", "mailto:", "javascript:"))
                            and abs_url != self.BASE_URL):
                        link = abs_url
                        break

            if not link or link in seen:
                continue
            seen.add(link)

            # Categoría y fecha
            cat_m = re.search(r"Categoría:\s*([^|]{0,80})", row_text, re.I)
            topic = clean_text(cat_m.group(1)) if cat_m else ""
            date = None
            d_m = re.search(r"Publicado desde:\s*([A-Za-zÁ-ú]{3,})\s+(\d{4})", row_text, re.I)
            if d_m:
                mon = MONTHS.get(d_m.group(1).lower()[:3])
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
                "url": link,
                "url_original": link,
            })

        # Respaldo: si no hubo filas, caza todos los PDFs de la página
        if not guides:
            for a in soup.select("a[href]"):
                if ".pdf" in a["href"].lower():
                    t = clean_text(a.get_text(" ", strip=True)) or "Guía CCN-CERT"
                    if is_junk(t):
                        continue
                    guides.append({
                        "id": f"guide_ccn_{len(guides)+1:03d}",
                        "source": self.SOURCE_ID,
                        "type": "guide",
                        "category": "ciberseguridad_conceptos",
                        "topic": self._code(t),
                        "title": t,
                        "summary": "",
                        "published_date": None,
                        "tags": ["CCN-CERT", "guía", "ciberseguridad"],
                        "url": urljoin(self.BASE_URL, a["href"]),
                        "url_original": urljoin(self.BASE_URL, a["href"]),
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
