"""Scraper de CCN-CERT."""
from bs4 import BeautifulSoup
from .base import BaseScraper


class CCNCertScraper(BaseScraper):
    SOURCE_ID = "ccn_cert"
    BASE_URL = "https://www.ccn-cert.cni.es/es/sobre-nosotros/faq.html"

    def scrape(self) -> list:
        html = self.fetch(self.BASE_URL)
        if not html:
            return []

        soup = BeautifulSoup(html, "lxml")
        faqs = []

        for i, q in enumerate(soup.select("h3, .faq-question")):
            answer_parts = []
            for sib in q.find_next_siblings():
                if sib.name in ("h3", "h2"):
                    break
                if sib.name in ("p", "li", "ul"):
                    answer_parts.append(sib.get_text(" ", strip=True))

            question = q.get_text(" ", strip=True)
            if not question:
                continue

            faqs.append({
                "id": f"{self.SOURCE_ID}_{i+1:02d}",
                "source": self.SOURCE_ID,
                "category": "ciberseguridad_conceptos",
                "tags": ["CCN-CERT", "ciberseguridad"],
                "question": question,
                "answer": " ".join(answer_parts)[:2000],
                "url_original": self.BASE_URL,
            })

        print(f"  ✅ CCN-CERT: {len(faqs)} FAQs")
        return faqs
