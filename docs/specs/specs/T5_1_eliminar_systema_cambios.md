# TASK T5.1: REFACTORIZACIÓN HACIA SISTEMA DE COINCIDENCIA ESTRICTA (STRICT MATCH)

## 🎯 OBJETIVO
Simplificar el motor de aplicación de cambios eliminando la lógica de "búsqueda flexible" y el historial de snapshots en `_changes`. El sistema ahora debe exigir una coincidencia exacta del 100% entre el bloque solicitado y el archivo físico.

## 🛠️ CAMBIOS REQUERIDOS

### 1. Refactorización en `domain/models.py` (o motor de aplicación):
- **Eliminar Búsqueda Flexible:** Eliminar cualquier uso de `re.sub` con flags de flexibilidad o reemplazos de espacios en blanco `\s+` que intenten "adivinar" el código.
- **Validación Estricta:** Implementar una comprobación binaria:
  ```python
  if search_block not in original_content:
      raise Exception("ERROR_MATCH: El código a reemplazar no existe exactamente igual en el archivo.")