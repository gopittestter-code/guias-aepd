"""Scraper de la AEPD."""
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from .base import BaseScraper


class AEPDScraper(BaseScraper):
    SOURCE_ID = "aepd"
    BASE_URL = "https://www.aepd.es/preguntas-frecuentes"

    CATEGORY_MAP = {
        "conceptos": "conceptos", "derechos": "derechos",
        "obligaciones": "obligaciones", "laboral": "obligaciones",
        "dpd": "dpd", "videovigilancia": "video",
        "menores": "menores", "reclamaciones": "reclamaciones",
        "internet": "internet",
    }

    def scrape(self) -> list:
        html = self.fetch(self.BASE_URL)
        if not html:
            return []

        soup = BeautifulSoup(html, "lxml")
        faqs = []
        seen_urls = set()
        cat_urls = []

        for a in soup.select("a[href*='/preguntas-frecuentes/']"):
            href = urljoin(self.BASE_URL, a.get("href", ""))
            if href not in seen_urls and href != self.BASE_URL:
                seen_urls.add(href)
                cat_urls.append(href)

        counter = 1
        for cat_url in cat_urls[:20]:
            cat_html = self.fetch(cat_url)
            if not cat_html:
                continue
            cat_soup = BeautifulSoup(cat_html, "lxml")

            for item in cat_soup.select("h2, h3"):
                q_text = item.get_text(" ", strip=True)
                if not q_text or len(q_text) < 10:
                    continue
                answer_parts = []
                for sib in item.find_next_siblings():
                    if sib.name in ("h2", "h3"):
                        break
                    if sib.name in ("p", "li"):
                        answer_parts.append(sib.get_text(" ", strip=True))
                    if len(answer_parts) >= 3:
                        break

                faqs.append({
                    "id": f"{self.SOURCE_ID}_{counter:03d}",
                    "source": self.SOURCE_ID,
                    "category": self._guess_category(cat_url),
                    "tags": ["AEPD", "RGPD"],
                    "question": q_text,
                    "answer": " ".join(answer_parts)[:2000],
                    "url_original": cat_url,
                })
                counter += 1

        print(f"  ✅ AEPD: {len(faqs)} FAQs")
        return faqs

    def _guess_category(self, url: str) -> str:
        for key, cat_id in self.CATEGORY_MAP.items():
            if key in url:
                return cat_id
        return "conceptos"
