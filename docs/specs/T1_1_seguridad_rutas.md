# SPEC-T1.1: VALIDACIÓN DE RUTAS Y SEGURIDAD

## 1. CONTEXTO
Actualmente, el sistema recibe una ruta de archivo (`file_path`) desde un LLM y realiza operaciones de sistema (borrar, escribir, leer). Existe el riesgo de que una alucinación de la IA acceda a archivos fuera del proyecto.

## 2. REQUERIMIENTOS FUNCIONALES
- Crear una función estática o utilidad `is_safe_path(base_path, target_path)`.
- La función debe retornar un booleano (`True`/`False`).
- Debe usar `os.path.abspath` y `os.path.commonpath` para validar la jerarquía.

## 3. LÓGICA DE CONTROL
1. Obtener la ruta absoluta del directorio raíz del proyecto.
2. Obtener la ruta absoluta del archivo objetivo.
3. Verificar si la ruta del archivo objetivo comienza con la ruta del directorio raíz.
4. Si un archivo está fuera del límite, lanzar `ChangeError` con un mensaje descriptivo.

## 4. PUNTOS DE APLICACIÓN (TARGETS)
- **`domain/models.py`**: En el método `apply_change` de la clase `Change`.
- **`services/project_service.py`**: En cualquier método que maneje borrado de carpetas.