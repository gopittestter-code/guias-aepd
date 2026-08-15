"""Scraper del EDPS."""
from bs4 import BeautifulSoup
from .base import BaseScraper


class EDPSscraper(BaseScraper):
    SOURCE_ID = "edps"
    BASE_URL = "https://www.edps.europa.eu/frequently-asked-questions_en"

    def scrape(self) -> list:
        html = self.fetch(self.BASE_URL)
        if not html:
            return []

        soup = BeautifulSoup(html, "lxml")
        faqs = []

        for i, q in enumerate(soup.select("h2, h3")):
            q_text = q.get_text(" ", strip=True)
            if not q_text or q_text.lower() in ("frequently asked questions", "faq"):
                continue

            answer_parts = []
            for sib in q.find_next_siblings():
                if sib.name in ("h2", "h3"):
                    break
                if sib.name in ("p", "li"):
                    answer_parts.append(sib.get_text(" ", strip=True))

            faqs.append({
                "id": f"{self.SOURCE_ID}_{i+1:02d}",
                "source": self.SOURCE_ID,
                "category": "conceptos",
                "tags": ["EDPS", "EU", "RGPD"],
                "question": q_text,
                "answer": " ".join(answer_parts)[:2000],
                "url_original": self.BASE_URL,
            })

        print(f"  ✅ EDPS: {len(faqs)} FAQs")
        return faqs
