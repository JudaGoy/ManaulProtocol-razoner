# SPEC-T3.1: BUCLE DE RETROALIMENTACIÓN (FEEDBACK LOOP)

## 1. CONTEXTO
Actualmente, si un cambio falla, el usuario debe leer el error y pedirle manualmente a la IA que lo intente de nuevo. Queremos automatizar este proceso para que el sistema genere un "Reporte de Fallo" que la IA pueda procesar inmediatamente.

## 2. REQUERIMIENTOS FUNCIONALES
- Implementar un formateador de errores que convierta las excepciones `ChangeError` en un bloque de texto estructurado.
- El reporte debe incluir: Tipo de error, Archivo, y el "Fragmento de contexto" que causó el conflicto.

## 3. LÓGICA DE CONTROL
1. **Captura de Excepción:** En el flujo principal, si `apply_change` lanza un `ChangeError`, no detener el programa.
2. **Generación de Prompt de Corrección:** Crear una función `generate_error_report(error)` que devuelva un mensaje como:
   > "ERROR DE APLICACIÓN: El bloque <codigo_antiguo> no coincide con el archivo [ruta]. 
   > Sugerencia: Revisa si hay espacios extra o si el archivo fue modificado por otra tarea."
3. **Reintento Automático (Opcional):** Preparar el terreno para que el servicio pueda reenviar este reporte a la IA en el siguiente turno.

## 4. PUNTOS DE APLICACIÓN (TARGETS)
- **`services/project_service.py`**: Donde se coordinan los cambios.
- **`domain/models.py`**: Añadir el método `to_dict()` o similar a `ChangeError`.