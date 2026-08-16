#!/usr/bin/env python3
"""FAQ Hub — Scraper principal (FAQs + Guías AEPD y CCN-CERT)."""
import json
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sources import ALL_SCRAPERS
from sources.base import is_junk, norm

OUTPUT = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "data", "faq_data.json"
)

META = {
    "version": "2.0.0",
    "title": "Base de Conocimiento de Protección de Datos y Seguridad de la Información",
    "description": "FAQs y guías oficiales recopiladas de fuentes internacionales",
    "languages": ["es", "en"],
}

SOURCES = [
    {"id": "aepd", "name": "AEPD (FAQs)", "country": "España", "url": "https://www.aepd.es/preguntas-frecuentes"},
    {"id": "aepd_guides", "name": "AEPD (Guías)", "country": "España", "url": "https://www.aepd.es/guias-y-herramientas/guias"},
    {"id": "ccn_cert", "name": "CCN-CERT (FAQs)", "country": "España", "url": "https://www.ccn-cert.cni.es/es/sobre-nosotros/faq.html"},
    {"id": "ccn_cert_guides", "name": "CCN-CERT (Guías)", "country": "España", "url": "https://www.ccn-cert.cni.es/es/guias.html"},
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
    {"id": "nis2", "name": "Directiva NIS2 / ENS", "icon": "📋"},
    {"id": "nis", "name": "Marcos y frameworks", "icon": "🏗️"},
    {"id": "ransomware", "name": "Ransomware", "icon": "🔒"},
]


def load_existing():
    """Carga el JSON actual filtrando basura."""
    try:
        with open(OUTPUT, "r", encoding="utf-8") as f:
            data = json.load(f)
        faqs = [f for f in data.get("faqs", []) if not is_junk(f.get("question", ""))]
        guides = [g for g in data.get("guides", []) if not is_junk(g.get("title", ""))]
        return faqs, guides
    except (FileNotFoundError, json.JSONDecodeError):
        return [], []


def guide_quality(g):
    """Puntúa qué tan buena es una guía (para no empeorar datos al fusionar)."""
    url = (g.get("url") or g.get("url_original") or "")
    s = 0
    if url and ".pdf" in url.lower():
        s += 3
    elif url and not url.rstrip("/").endswith(("guias.html", "/guias", "faq.html")):
        s += 2
    if g.get("summary"):
        s += 1
    if g.get("published_date"):
        s += 1
    return s


def merge_faqs(existing, new):
    """Fusiona FAQs por pregunta; prefiere respuestas más largas."""
    by_id = {f["id"]: f for f in existing}
    by_q = {norm(f["question"]): f for f in existing}
    for f in new:
        if is_junk(f.get("question", "")):
            continue
        q = norm(f["question"])
        old = by_q.get(q)
        if old:
            # Siempre preferir la respuesta más larga
            if len(f.get("answer", "")) > len(old.get("answer", "")):
                merged = dict(f); merged["id"] = old["id"]
                by_id[old["id"]] = merged
                by_q[q] = merged
        else:
            by_id[f["id"]] = f
            by_q[q] = f
    return list(by_id.values())


def merge_guides(existing, new):
    """Fusiona guías por título; nunca empeora una guía buena."""
    by_id = {g["id"]: g for g in existing}
    by_t = {norm(g["title"]): g for g in existing}
    for g in new:
        if is_junk(g.get("title", "")):
            continue
        t = norm(g["title"])
        old = by_t.get(t)
        if old:
            # 🔧 Nunca sustituir una guía buena por una peor
            if guide_quality(old) > guide_quality(g):
                continue
            merged = dict(g); merged["id"] = old["id"]
            by_id[old["id"]] = merged
            by_t[t] = merged
        else:
            by_id[g["id"]] = g
            by_t[t] = g
    # Ordenar por fecha descendente
    items = list(by_id.values())
    items.sort(key=lambda x: x.get("published_date") or "0000-00-00", reverse=True)
    return items


def main():
    print("🤖 FAQ Hub v2.0 — Actualizando base de conocimiento\n")

    all_faqs = []
    all_guides = []
    for scraper_cls in ALL_SCRAPERS:
        try:
            items = scraper_cls().scrape()
            if items and items[0].get("type") == "guide":
                all_guides.extend(items)
            else:
                all_faqs.extend(items)
        except Exception as e:
            print(f"  ❌ Error en {scraper_cls.__name__}: {e}")
            import traceback
            traceback.print_exc()

    existing_faqs, existing_guides = load_existing()
    merged_faqs = merge_faqs(existing_faqs, all_faqs)
    merged_guides = merge_guides(existing_guides, all_guides)

    META["extracted_date"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    META["total_sources"] = len({f["source"] for f in merged_faqs + merged_guides})
    META["total_faqs"] = len(merged_faqs)
    META["total_guides"] = len(merged_guides)

    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(
            {"meta": META, "sources": SOURCES, "categories": CATEGORIES,
             "faqs": merged_faqs, "guides": merged_guides},
            f, ensure_ascii=False, indent=2,
        )

    print(f"\n✅ Listo: {len(merged_faqs)} FAQs + {len(merged_guides)} guías en {OUTPUT}")


if __name__ == "__main__":
    main()
