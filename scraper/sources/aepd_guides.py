"""Scraper de las guías oficiales publicadas por la AEPD."""
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from .base import BaseScraper, clean_text, is_junk


TOPIC_TO_CAT = {
    "internet y nuevas tecnologías": "internet",
    "cumplimiento (compliance)": "obligaciones",
    "privacidad y principios": "conceptos",
    "categorías especiales": "conceptos",
    "responsable del tratamiento": "obligaciones",
    "legislación": "conceptos",
    "datos de carácter personal": "conceptos",
    "seguridad/ciberseguridad": "ciberseguridad_conceptos",
    "ciberseguridad": "ciberseguridad_conceptos",
    "delitos en internet": "internet",
    "educación y menores": "menores",
    "ámbito laboral": "obligaciones",
    "derechos": "derechos",
    "videovigilancia": "video",
    "administración electrónica": "conceptos",
    "autoridades de control": "reclamaciones",
    "brechas de seguridad": "brechas",
    "transferencias internacionales": "conceptos",
    "publicidad": "internet",
    "reclamaciones": "reclamaciones",
}


class AEPDGuidesScraper(BaseScraper):
    SOURCE_ID = "aepd_guides"
    BASE_URL = "https://www.aepd.es/guias-y-herramientas/guias"

    def scrape(self):
        html = self.fetch(self.BASE_URL)
        if not html:
            return []

        soup = BeautifulSoup(html, "lxml")
        guides = []

        # Cada guía está dentro de un <article> o bloque con h3 (título) + fecha + enlace "Ver documento"
        for block in soup.select("article, .card, li"):
            h = block.select_one("h2, h3, h4")
            if not h:
                continue
            title = clean_text(h.get_text(" ", strip=True))
            if not title or is_junk(title):
                continue

            # Enlace al PDF
            link = None
            for a in block.select("a[href]"):
                href = a.get("href", "")
                if "/guias/" in href and href.lower().endswith(".pdf"):
                    link = urljoin(self.BASE_URL, href)
                    break
            if not link:
                a = block.select_one("a[href*='.pdf']")
                if a:
                    link = urljoin(self.BASE_URL, a["href"])

            # Fecha (formato "21 de Julio de 2026")
            date = None
            txt = block.get_text(" ")
            m = re.search(r"(\d{1,2})\s+de\s+([A-Za-zÁ-ú]+)\s+de\s+(\d{4})", txt, re.I)
            if m:
                day, mon_txt, year = m.groups()
                months = {
                    "enero":1,"febrero":2,"marzo":3,"abril":4,"mayo":5,"junio":6,
                    "julio":7,"agosto":8,"septiembre":9,"octubre":10,"noviembre":11,"diciembre":12,
                }
                mon = months.get(mon_txt.lower(), 0)
                if mon:
                    date = f"{year}-{mon:02d}-{int(day):02d}"

            # Descripción breve (primer párrafo no título/fecha)
            summary_parts = []
            for p in block.select("p"):
                t = clean_text(p.get_text(" ", strip=True))
                if not t or t == title:
                    continue
                if re.match(r"^\d{1,2}\s+de\s+\w+\s+de\s+\d{4}$", t, re.I):
                    continue
                summary_parts.append(t)
                if len(summary_parts) >= 2:
                    break
            summary = " ".join(summary_parts)[:400]

            # Tema (primer texto con palabra clave antes del título o en un span)
            topic = ""
            for tag in block.select("span, small, .topic, .category"):
                t = clean_text(tag.get_text(" ", strip=True))
                if 5 < len(t) < 80 and t != title:
                    topic = t
                    break

            guides.append({
                "id": f"guide_{len(guides)+1:03d}",
                "source": self.SOURCE_ID,
                "type": "guide",
                "category": self._topic_to_cat(topic or title),
                "topic": topic,
                "title": title,
                "summary": summary,
                "published_date": date,
                "tags": ["AEPD", "guía", "oficial"],
                "url": link or self.BASE_URL,
                "url_original": link or self.BASE_URL,
            })

        print(f"  ✅ AEPD Guías: {len(guides)} documentos")
        return guides

    def _topic_to_cat(self, text):
        text_l = text.lower()
        for key, cat in TOPIC_TO_CAT.items():
            if key in text_l:
                return cat
        return "conceptos"
