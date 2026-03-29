# SPEC-T3.2: LOG DE AUDITORÍA Y REGISTRO DE CAMBIOS

## 1. CONTEXTO
Actualmente, una vez que se aplican los cambios, no queda un registro histórico permanente de qué archivos fueron modificados, qué acciones se realizaron o qué errores ocurrieron, a menos que el usuario lo copie manualmente de la consola.

## 2. REQUERIMIENTOS FUNCIONALES
- Crear un sistema de logging persistente en un archivo llamado `manaul_protocol.log` en la raíz del proyecto.
- Registrar cada intento de cambio, incluyendo: Timestamp, Archivo, Acción, Resultado (ÉXITO/ERROR) y, en caso de error, el tipo de `ChangeError`.

## 3. LÓGICA DE CONTROL
1. **Inicialización:** Configurar el módulo `logging` de Python para escribir en modo "append" (añadir al final).
2. **Formato de Registro:** `[2023-10-27 10:00:05] [SUCCESS] CREATE: domain/new_model.py`
   `[2023-10-27 10:00:08] [ERROR] PATCH: services/auth.py - Motivo: Bloque no encontrado`
3. **Persistencia:** El log debe guardarse incluso si la aplicación se cierra inesperadamente.

## 4. PUNTOS DE APLICACIÓN (TARGETS)
- **`services/project_service.py`**: Integrar las llamadas de log dentro del bucle de `accept_all_changes`.