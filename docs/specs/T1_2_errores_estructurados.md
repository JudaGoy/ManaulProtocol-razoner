# SPEC-T1.2: MANEJO DE ERRORES ESTRUCTURADO

## 1. CONTEXTO
El sistema actual utiliza `print()` para reportar fallos en la aplicación de cambios y devuelve `False` de forma genérica. Esto dificulta la depuración automática y no proporciona feedback útil al LLM cuando un parche falla.

## 2. REQUERIMIENTOS FUNCIONALES
- Estandarizar el uso de la clase `ChangeError` (ya existente en `models.py`).
- Eliminar los `print()` dentro de la lógica de negocio y sustituirlos por excepciones.
- Mejorar el feedback cuando un "bloque de código antiguo" no coincide con el archivo real.

## 3. LÓGICA DE CONTROL
1. **Validación de Contenido:** Si `_apply_text_change_as_patch` no encuentra el bloque de código original, debe lanzar `ChangeError` con un mensaje que incluya: "Error de coincidencia: El bloque de código antiguo no existe en el archivo [ruta]".
2. **Jerarquía de Errores:** - Si es un problema de permisos: `ChangeError("Permisos insuficientes para modificar [archivo]")`.
   - Si el archivo no existe: `ChangeError("Archivo no encontrado: [archivo]")`.
3. **Captura en el Flujo Principal:** Asegurar que el bucle que procesa la lista de cambios capture estas excepciones y las guarde en un log o las muestre de forma agrupada al final, en lugar de detener todo el programa abruptamente.

## 4. PUNTOS DE APLICACIÓN (TARGETS)
- **`domain/models.py`**: Principalmente en los métodos `apply_change` y las funciones auxiliares de parcheo de texto.