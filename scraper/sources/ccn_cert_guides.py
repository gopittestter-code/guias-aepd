"""Scraper de las guías oficiales publicadas por el CCN-CERT."""
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from .base import BaseScraper, clean_text, is_junk


# Mapeo de temas/series del CCN a categorías del sistema
TOPIC_TO_CAT = {
    "stic": "ciberseguridad_conceptos",
    "stic-": "ciberseguridad_conceptos",
    "guía": "ciberseguridad_conceptos",
    "crip": "ciberseguridad_conceptos",
    "ccn-cert": "ciberseguridad_conceptos",
    "incidente": "incidentes",
    "ransomware": "ransomware",
    "nis": "nis2",
    "ens": "nis2",
    "certificación": "ciberseguridad_conceptos",
    "seguridad nacional": "ciberseguridad_conceptos",
    "ciberseguridad": "ciberseguridad_conceptos",
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
        seen_ids = set()

        # El CCN-CERT lista las guías como artículos/tarjetas con enlaces a PDF
        # Buscamos todos los bloques que contengan un enlace a un PDF de guía
        for block in soup.select("article, li, .item, .guide-item, .card, div"):
            # Busca enlaces a PDFs del CCN
            pdf_link = None
            for a in block.select("a[href]"):
                href = a.get("href", "")
                if href.lower().endswith(".pdf") and ("guias" in href.lower() or "ccn-cert" in href.lower() or "/es/" in href):
                    pdf_link = urljoin(self.BASE_URL, href)
                    break

            if not pdf_link:
                continue

            # Evitar duplicados por PDF
            if pdf_link in seen_ids:
                continue
            seen_ids.add(pdf_link)

            # Título: el h2/h3/h4 más cercano, o el texto del enlace
            title_el = block.select_one("h2, h3, h4, .title")
            if title_el:
                title = clean_text(title_el.get_text(" ", strip=True))
            else:
                # Usa el primer enlace con texto significativo
                a = block.select_one("a")
                title = clean_text(a.get_text(" ", strip=True)) if a else ""

            if not title or is_junk(title):
                continue

            # Código de la guía (STIC-XXX, CCN-CERT-XXX, etc.)
            code_match = re.search(r"\b([A-Z]+-\d+[A-Z0-9-]*)\b", title)
            code = code_match.group(1) if code_match else ""

            # Resumen: primer párrafo que no sea el título ni un código
            summary = ""
            for p in block.select("p"):
                t = clean_text(p.get_text(" ", strip=True))
                if not t or t == title or len(t) < 20:
                    continue
                if re.match(r"^[A-Z]+-\d+", t):
                    continue
                summary = t[:400]
                break

            # Fecha si existe
            date = None
            txt = block.get_text(" ")
            m = re.search(r"(\d{1,2})[/-](\d{1,2})[/-](\d{4})", txt)
            if m:
                d, mo, y = m.groups()
                date = f"{y}-{int(mo):02d}-{int(d):02d}"
            else:
                m = re.search(r"(\d{4})", txt)
                if m and 2010 <= int(m.group(1)) <= 2030:
                    date = f"{m.group(1)}-01-01"

            # Tema y categoría
            topic = code or self._extract_topic(title)
            category = self._topic_to_cat(topic + " " + title)

            guides.append({
                "id": f"guide_ccn_{len(guides)+1:03d}",
                "source": self.SOURCE_ID,
                "type": "guide",
                "category": category,
                "topic": topic,
                "title": title,
                "summary": summary,
                "published_date": date,
                "tags": ["CCN-CERT", "guía", "ciberseguridad", "oficial"],
                "url": pdf_link,
                "url_original": pdf_link,
            })

        print(f"  ✅ CCN-CERT Guías: {len(guides)} documentos")
        return guides

    def _extract_topic(self, title):
        # Extrae un "tema" legible del título
        t = title
        # Si empieza por código STIC-123, quítalo
        t = re.sub(r"^[A-Z]+-\d+[A-Z0-9-]*[:\s]*", "", t).strip()
        return t[:80] if t else title[:80]

    def _topic_to_cat(self, text):
        text_l = text.lower()
        for key, cat in TOPIC_TO_CAT.items():
            if key in text_l:
                return cat
        return "ciberseguridad_conceptos"
