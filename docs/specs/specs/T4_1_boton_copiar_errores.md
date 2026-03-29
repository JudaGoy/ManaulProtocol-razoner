# SPEC-T4.1: BOTÓN DE COPIADO RÁPIDO DE ERRORES

## 1. CONTEXTO
Tras procesar una lista de cambios, si existen errores, el sistema genera un reporte. Necesitamos un botón en la interfaz de "Gestión de Cambios" que aparezca solo si hay errores y permita copiar todo el reporte al portapapeles con un clic.

## 2. REQUERIMIENTOS FUNCIONALES
- Añadir un botón `Copiar Reporte de Errores` en la parte inferior de la ventana `ChangeManagementWindow`.
- El botón debe usar `pyperclip` (o la librería estándar de Tkinter) para enviar el texto al portapapeles.
- Notificar al usuario con un mensaje temporal o un cambio de color en el botón ("¡Copiado!").

## 3. LÓGICA DE CONTROL
1. **Visibilidad:** El botón debe estar deshabilitado o invisible si la lista `failed_errors` está vacía.
2. **Formateo:** Al hacer clic, debe llamar a `get_failed_tasks_report(failed_errors)` y copiar el resultado.
3. **Feedback:** Mostrar un pequeño mensaje de confirmación para que el usuario sepa que ya puede ir al chat de la IA a pegar.

## 4. PUNTOS DE APLICACIÓN (TARGETS)
- **`ui/windows/change_management_window.py`**: Interfaz visual (Tkinter/CustomTkinter).
- **`ui/windows/change_management_controller.py`**: Lógica de enlace.