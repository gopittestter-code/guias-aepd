"""Scraper de INCIBE — Línea de Ayuda en Ciberseguridad (017)."""
from bs4 import BeautifulSoup
from .base import BaseScraper


class IncibeScraper(BaseScraper):
    SOURCE_ID = "incibe"
    BASE_URL = "https://www.incibe.es/linea-de-ayuda-en-ciberseguridad/faq"

    def scrape(self) -> list:
        html = self.fetch(self.BASE_URL)
        if not html:
            return []

        soup = BeautifulSoup(html, "lxml")
        faqs = []

        for i, item in enumerate(soup.select(".faq-item, .accordion-item, article")):
            q_el = item.select_one("h2, h3, .faq-question, button")
            a_el = item.select_one(".faq-answer, .accordion-content, p")
            if not q_el:
                continue

            faqs.append({
                "id": f"{self.SOURCE_ID}_{i+1:02d}",
                "source": self.SOURCE_ID,
                "category": "ciberseguridad_conceptos",
                "tags": ["INCIBE", "017", "ayuda"],
                "question": q_el.get_text(" ", strip=True),
                "answer": (a_el.get_text(" ", strip=True) if a_el else "")[:2000],
                "url_original": self.BASE_URL,
            })

        print(f"  ✅ INCIBE: {len(faqs)} FAQs")
        return faqs
