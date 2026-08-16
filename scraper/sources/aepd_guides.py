"""Scraper de las guías oficiales de la AEPD (con PDF directo)."""
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from .base import BaseScraper, clean_text, is_junk

MONTHS = {
    "enero":1,"febrero":2,"marzo":3,"abril":4,"mayo":5,"junio":6,
    "julio":7,"agosto":8,"septiembre":9,"octubre":10,"noviembre":11,"diciembre":12,
}

TOPIC_TO_CAT = {
    "internet y nuevas tecnologías": "internet",
    "cumplimiento": "obligaciones",
    "privacidad": "conceptos",
    "categorías especiales": "conceptos",
    "responsable del tratamiento": "obligaciones",
    "legislación": "conceptos",
    "seguridad/ciberseguridad": "ciberseguridad_conceptos",
    "ciberseguridad": "ciberseguridad_conceptos",
    "delitos en internet": "internet",
    "educación y menores": "menores",
    "ámbito laboral": "obligaciones",
    "derechos": "derechos",
    "videovigilancia": "video",
    "brechas de seguridad": "brechas",
    "transferencias internacionales": "conceptos",
    "publicidad": "internet",
    "reclamaciones": "reclamaciones",
}


class AEPDGuidesScraper(BaseScraper):
    SOURCE_ID = "aepd_guides"
    BASE_URL = "https://www.aepd.es/guias-y-herramientas/guias"

    def scrape(self):
        html = self.fetch_rendered(self.BASE_URL)
        if not html:
            return []

        soup = BeautifulSoup(html, "lxml")
        guides = []
        seen = set()

        for block in soup.select("article, .card, li, .views-row, div"):
            h = block.select_one("h2, h3, h4")
            if not h:
                continue
            title = clean_text(h.get_text(" ", strip=True))
            if not title or is_junk(title) or title in seen:
                continue

            # 1) PDF directo dentro del bloque
            link = None
            for a in block.select("a[href]"):
                if ".pdf" in a["href"].lower():
                    link = urljoin(self.BASE_URL, a["href"])
                    break

            # 2) Si no, seguir "Ver documento" y buscar el PDF dentro
            if not link:
                doc = block.select_one("a[href*='guias'], a[href*='node']")
                if doc:
                    node_url = urljoin(self.BASE_URL, doc["href"])
                    node_html = self.fetch(node_url)
                    if node_html:
                        ns = BeautifulSoup(node_html, "lxml")
                        pa = ns.select_one("a[href*='.pdf']")
                        if pa:
                            link = urljoin(node_url, pa["href"])

            if not link:
                continue
            seen.add(title)

            # Fecha
            date = None
            m = re.search(r"(\d{1,2})\s+de\s+([A-Za-zÁ-ú]+)\s+de\s+(\d{4})", block.get_text(" "), re.I)
            if m:
                mon = MONTHS.get(m.group(2).lower())
                if mon:
                    date = f"{m.group(3)}-{mon:02d}-{int(m.group(1)):02d}"

            # Tema
            topic = ""
            for tag in block.select("span, small, .topic, .category"):
                t = clean_text(tag.get_text(" ", strip=True))
                if 5 < len(t) < 80 and t != title:
                    topic = t
                    break

            # Resumen
            summary = ""
            for p in block.select("p"):
                t = clean_text(p.get_text(" ", strip=True))
                if t and t != title and not re.match(r"^\d{1,2}\s+de\s+\w+\s+de\s+\d{4}$", t, re.I):
                    summary = t[:400]
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
                "url": link,
                "url_original": link,
            })

        print(f"  ✅ AEPD Guías: {len(guides)} documentos")
        return guides

    def _topic_to_cat(self, text):
        tl = text.lower()
        for k, v in TOPIC_TO_CAT.items():
            if k in tl:
                return v
        return "conceptos"
