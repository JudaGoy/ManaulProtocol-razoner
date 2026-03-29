# SPEC-T2.1: PARSER XML ROBUSTO CON BEAUTIFULSOUP

## 1. CONTEXTO
El sistema actual usa `re.search` para extraer bloques `<CAMBIOS>`. Esto es frágil si el LLM incluye texto extra, olvida cerrar una etiqueta o usa bloques de código Markdown (```xml). Necesitamos un parser real que sea tolerante a errores.

## 2. REQUERIMIENTOS FUNCIONALES
- Sustituir el motor de búsqueda de texto por `BeautifulSoup` con el parser `lxml-xml` o `html.parser`.
- Extraer de forma precisa todos los elementos `<ARCHIVO>` y sus hijos: `<accion>`, `<file_path>`, `<codigo_antiguo>`, `<codigo_nuevo>`.

## 3. LÓGICA DE CONTROL
1. **Extracción Multitarea:** El parser debe encontrar todos los bloques de cambios en una sola respuesta, no solo el primero.
2. **Tolerancia:** Si una etiqueta opcional como `<codigo_antiguo>` no viene en el XML (común en acciones de "crear"), el sistema debe asignar un string vacío `""` en lugar de fallar.
3. **Limpieza de Markdown:** El sistema debe detectar si el XML está envuelto en triple comilla inversa (```xml ... ```) y extraer el contenido interior antes de parsear.

## 4. PUNTOS DE APLICACIÓN (TARGETS)
- **`domain/models.py`**: Función `parse_xml_content`.