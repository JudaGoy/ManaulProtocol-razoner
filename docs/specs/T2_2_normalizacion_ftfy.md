# SPEC-T2.2: NORMALIZACIÓN DE TEXTO CON FTFY

## 1. CONTEXTO
Los LLM a veces devuelven código con codificaciones mezcladas (UTF-8, Latin-1) o caracteres de control invisibles que rompen el parcheo de texto. Necesitamos que el sistema "limpie" el contenido antes de intentar compararlo con los archivos locales.

## 2. REQUERIMIENTOS FUNCIONALES
- Integrar la librería `ftfy` (Fix Text For You).
- Crear una función de utilidad `normalize_code_text(text)` en `domain/models.py`.
- Aplicar esta limpieza tanto al código que viene de la IA como al contenido que leemos del disco duro.

## 3. LÓGICA DE CONTROL
1. **Limpieza Automática:** Usar `ftfy.fix_text()` para reparar mojibake (caracteres rotos).
2. **Consistencia de Saltos de Línea:** Convertir todos los finales de línea a `\n` (estándar Unix) para evitar que un archivo guardado en Windows falle al compararse con uno de Linux.
3. **Espacios en Blanco:** Eliminar espacios accidentales al final de las líneas que la IA suele añadir por error.

## 4. PUNTOS DE APLICACIÓN (TARGETS)
- **`domain/models.py`**: Antes de que `_apply_text_change_as_patch` haga el `.replace()`.