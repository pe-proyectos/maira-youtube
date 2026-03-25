# PRODUCTION RULES — Maira YouTube Shorts

## Formato
- **Orientación:** Vertical 9:16
- **Resolución:** 1080x1920 (Full HD)
- **FPS:** 30
- **Duración máxima:** 60 segundos (incluyendo los 5s finales)

## Estructura del Video
1. **Intro** — PNGtuber Maira (Asa Mitaka, blanco y negro) con catchphrase
2. **Desarrollo** — Imágenes del anime con narración
3. **Cierre emocional** — Reflexión + esperanza
4. **5 segundos finales** — Sin voz, última imagen sigue animada (Ken Burns), música sigue SIN fade out. Corte limpio al final. Para que el espectador procese y el loop sea natural.

## Visual
- **Fondo:** Blanco (#ffffff) — NO negro
- **Overlay:** rgba(0,0,0,0.3) sobre imágenes para legibilidad de texto
- **PNGtuber:** Paneles manga de Asa Mitaka en blanco y negro (diferentes expresiones)
- **Transiciones:** xfade (dissolve, fadeblack, slideleft) entre segmentos
- **Efectos de imagen:** Ken Burns (zoom/pan lento), shake para impacto

## Audio
- **TTS:** ElevenLabs v3, voice ID FvmvwvObRqIHojkEGh5N
- **TTS settings:** stability 0.35, similarity_boost 0.8, style 0.6, speed 1.15
- **Música:** SIEMPRE covers en latino/español del anime del video
- **Tono musical:** Debe matchear el contenido emocional
- **BGM volume:** ~12% debajo de la voz
- **BGM fade:** Fade in al inicio (2s), SIN fade out al final
- **5s finales:** Música sigue sonando normal, sin voz

## Subtítulos
- **Estilo:** Karaoke, 3-5 palabras por frase
- **Highlight:** Word-by-word (palabra activa resaltada)
- **Efectos:** Impacto visual en palabras emocionales
- **Formato:** ASS con fuente Montserrat Black

## Guión
- **Catchphrase:** "Me vas a odiar, pero..." (+ 10 variaciones)
- **Estructura narrativa:** Opinión controversial → reflexión profunda → esperanza
- **TTS reglas de puntuación:**
  - Sin puntos suspensivos (...)
  - Comas solo para pausas reales
  - Puntos solo entre ideas distintas
  - Puntuación al servicio del audio, no de la gramática

## Flujo de Producción
1. **Guión** — Escribir texto del short
2. **Guión visual** — Mapear imágenes a cada momento del audio
3. **Voice over** — Generar TTS con ElevenLabs (con timestamps)
4. **Composición** — Render con FFmpeg (script determinista, correr en background)
5. **Preview** — Enviar preview comprimido por Discord
6. **Feedback** — Shoko revisa y da cambios
7. **Render final** — Aplicar cambios, render definitivo
8. **Entrega** — Archivo final a Shoko, él sube a YouTube

## Assets
- Organizados por tema: `assets/<anime>/images/`, `assets/<anime>/music/`
- Descargar música con `scripts/y2mate-download.sh`
- NO pushear videos grandes a GitHub

## Reglas Técnicas
- Scripts largos → correr en **background**, nunca bloquearse
- Scripts deterministas (.sh/.py) para tareas repetibles
- Sub-agentes para trabajo pesado, verificar output
- Previews comprimidos para Discord (< 8MB, 540p)
