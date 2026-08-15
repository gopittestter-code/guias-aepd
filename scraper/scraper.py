#!/usr/bin/env python3
"""
FAQ Hub — Scraper principal
Recorre todas las fuentes oficiales y regenera data/faq_data.json.
"""
import json
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sources import ALL_SCRAPERS

OUTPUT = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "data", "faq_data.json"
)

META = {
    "version": "1.0.0",
    "title": "Base de Conocimiento de Protección de Datos y Seguridad de la Información",
    "description": "FAQs recopiladas automáticamente de fuentes oficiales internacionales",
    "languages": ["es", "en"],
}

SOURCES = [
    {"id": "aepd", "name": "AEPD", "country": "España", "url": "https://www.aepd.es/preguntas-frecuentes"},
    {"id": "ccn_cert", "name": "CCN-CERT", "country": "España", "url": "https://www.ccn-cert.cni.es/es/sobre-nosotros/faq.html"},
    {"id": "incibe", "name": "INCIBE", "country": "España", "url": "https://www.incibe.es/linea-de-ayuda-en-ciberseguridad/faq"},
    {"id": "edps", "name": "EDPS", "country": "Unión Europea", "url": "https://www.edps.europa.eu/frequently-asked-questions_en"},
    {"id": "edpb", "name": "EDPB", "country": "Unión Europea", "url": "https://www.edpb.europa.eu/contact/frequently-asked-questions_en"},
    {"id": "enisa", "name": "ENISA", "country": "Unión Europea", "url": "https://www.enisa.europa.eu"},
    {"id": "ico", "name": "ICO", "country": "Reino Unido", "url": "https://ico.org.uk"},
    {"id": "nist", "name": "NIST", "country": "Estados Unidos", "url": "https://www.nist.gov/cyberframework"},
    {"id": "cisa", "name": "CISA", "country": "Estados Unidos", "url": "https://www.cisa.gov"},
]

CATEGORIES = [
    {"id": "conceptos", "name": "Conceptos básicos", "icon": "🧭"},
    {"id": "derechos", "name": "Derechos de los afectados", "icon": "🛡️"},
    {"id": "obligaciones", "name": "Obligaciones del responsable", "icon": "🏢"},
    {"id": "dpd", "name": "Delegado de Protección de Datos", "icon": "👤"},
    {"id": "brechas", "name": "Brechas de datos", "icon": "🚨"},
    {"id": "video", "name": "Videovigilancia", "icon": "🎥"},
    {"id": "menores", "name": "Menores y educación", "icon": "🎓"},
    {"id": "internet", "name": "Internet y redes sociales", "icon": "🌐"},
    {"id": "reclamaciones", "name": "Reclamaciones", "icon": "📮"},
    {"id": "ciberseguridad_conceptos", "name": "Conceptos de ciberseguridad", "icon": "🛰️"},
    {"id": "incidentes", "name": "Gestión de incidentes", "icon": "🆘"},
    {"id": "nis2", "name": "Directiva NIS2", "icon": "📋"},
    {"id": "nis", "name": "Marcos y frameworks", "icon": "🏗️"},
    {"id": "ransomware", "name": "Ransomware", "icon": "🔒"},
]


def load_existing() -> list:
    try:
        with open(OUTPUT, "r", encoding="utf-8") as f:
            return json.load(f).get("faqs", [])
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def merge_faqs(existing, new):
    by_id = {f["id"]: f for f in existing}
    for f in new:
        by_id[f["id"]] = f
    return list(by_id.values())


def main():
    print("🤖 FAQ Hub — Actualizando base de conocimiento\n")

    all_new = []
    for scraper_cls in ALL_SCRAPERS:
        try:
            all_new.extend(scraper_cls().scrape())
        except Exception as e:
            print(f"  ❌ Error en {scraper_cls.__name__}: {e}")

    merged = merge_faqs(load_existing(), all_new)

    META["extracted_date"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    META["total_sources"] = len({f["source"] for f in merged})
    META["total_faqs"] = len(merged)

    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(
            {"meta": META, "sources": SOURCES, "categories": CATEGORIES, "faqs": merged},
            f, ensure_ascii=False, indent=2,
        )

    print(f"\n✅ Listo: {len(merged)} FAQs escritas en {OUTPUT}")


if __name__ == "__main__":
    main()
