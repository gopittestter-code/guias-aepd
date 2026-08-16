# 🛡️ FAQ Hub — Base de Conocimiento de Protección de Datos y Ciberseguridad

Aplicación web estática que reúne las preguntas frecuentes oficiales de organismos públicos
(AEPD, CCN-CERT, INCIBE, EDPS, EDPB, ENISA, ICO, NIST, CISA) en un único buscador.

**100% gratuito** — sin servidores, sin bases de datos, sin API keys.

## 🚀 Características

- 🔎 Búsqueda instantánea con resaltado de resultados (Fuse.js)
- 🗂️ Filtros por fuente y categoría  
- 📱 Diseño responsive (móvil, tablet y escritorio)
- ⚡ Carga de datos desde un único archivo JSON
- 🤖 Actualización automática semanal vía GitHub Actions

## 🌐 Demo

`https://TU-USUARIO.github.io/faq-hub/`

## 📊 Fuentes incluidas

| Fuente | País | Tipo |
|--------|------|------|
| AEPD | 🇪🇸 España | Protección de datos |
| CCN-CERT | 🇪🇸 España | Ciberseguridad |
| INCIBE | 🇪🇸 España | Ciberseguridad |
| EDPS / EDPB | 🇪🇺 UE | Protección de datos |
| ENISA | 🇪🇺 UE | Ciberseguridad |
| ICO | 🇬🇧 UK | Protección de datos |
| NIST / CISA | 🇺🇸 USA | Frameworks / Ciberseguridad |

## 🛠️ Stack tecnológico

- **Frontend:** HTML5 + CSS3 + JavaScript vanilla
- **Búsqueda:** Fuse.js (CDN gratuito)
- **Datos:** JSON estático (`data/faq_data.json`)
- **Hosting:** GitHub Pages (gratis)
- **Automatización:** GitHub Actions (gratis)
- **Scraping:** Python + requests + BeautifulSoup (open source)

## 🤖 Actualización automática

GitHub Actions ejecuta el scraper cada lunes a las 03:00 UTC y publica los cambios.

## ⚠️ Aviso legal

Este sitio no está afiliado a ninguno de los organismos citados. Las respuestas se muestran
como extracto; consulta siempre la fuente oficial para el texto íntegro y actualizado.
