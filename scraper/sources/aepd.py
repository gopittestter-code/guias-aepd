"""Scraper de la AEPD — captura respuesta COMPLETA (todos los párrafos)."""
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from .base import BaseScraper, clean_text, is_junk


class AEPDScraper(BaseScraper):
    SOURCE_ID = "aepd"
    BASE_URL = "https://www.aepd.es/preguntas-frecuentes"

    CATEGORY_MAP = {
        "0-conceptos": "conceptos",
        "1-tus-derechos": "derechos",
        "2-tus-obligaciones": "obligaciones",
        "3-proteccion": "obligaciones",
        "4-dpd": "dpd",
        "8-videovigilancia": "video",
        "10-menores": "menores",
        "13-reclamaciones": "reclamaciones",
        "17-internet": "internet",
    }

    def scrape(self):
        html = self.fetch(self.BASE_URL)
        if not html:
            return []

        soup = BeautifulSoup(html, "lxml")
        faqs = []
        seen = set()
        cat_urls = []

        # Recopilar URLs de categorías
        for a in soup.select("a[href*='/preguntas-frecuentes/']"):
            href = urljoin(self.BASE_URL, a.get("href", ""))
            if href not in seen and href != self.BASE_URL:
                seen.add(href)
                cat_urls.append(href)

        counter = 1
        for cat_url in cat_urls[:25]:
            cat_html = self.fetch(cat_url)
            if not cat_html:
                continue
            cat_soup = BeautifulSoup(cat_html, "lxml")

            for item in cat_soup.select("h2, h3"):
                q_text = clean_text(item.get_text(" ", strip=True))
                if not q_text or is_junk(q_text):
                    continue

                # 🔧 RECOGE TODOS los párrafos hasta el siguiente título
                answer_parts = []
                link = None
                for sib in item.find_next_siblings():
                    if sib.name in ("h2", "h3", "h1"):
                        break
                    # Captura enlaces a la FAQ oficial
                    if link is None:
                        a_tag = sib if sib.name == "a" else sib.find("a", href=True)
                        if a_tag and a_tag.get("href"):
                            link = urljoin(cat_url, a_tag["href"])
                    # Captura texto de p, li, div (muchas FAQs están en divs)
                    nodes = sib.find_all(["p", "li"]) if sib.name not in ("p", "li") else [sib]
                    for n in nodes:
                        t = clean_text(n.get_text(" ", strip=True))
                        if t and not t.lower().startswith("leer más"):
                            answer_parts.append(t)

                answer = " ".join(answer_parts)
                if not answer:
                    continue  # descarta preguntas sin respuesta

                faqs.append({
                    "id": f"{self.SOURCE_ID}_{counter:03d}",
                    "source": self.SOURCE_ID,
                    "category": self._guess_category(cat_url),
                    "tags": ["AEPD", "RGPD"],
                    "question": q_text,
                    "answer": answer,  # 🔧 Sin recorte: respuesta completa tal cual
                    "url_original": link or cat_url,
                })
                counter += 1

        print(f"  ✅ AEPD: {len(faqs)} FAQs")
        return faqs

    def _guess_category(self, url):
        for key, cat_id in self.CATEGORY_MAP.items():
            if key in url:
                return cat_id
        return "conceptos"
