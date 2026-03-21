import os
import re
import html
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from utils.git_manager import apply_patch_to_text


# Separador único para almacenar múltiples versiones en un solo archivo de historial.
HISTORY_SEPARATOR = "\n---_APPLY_HISTORY_VERSION_SEPARATOR_---\n"

def normalize_history_text(text: str) -> str:
    """Decodifica entidades XML y caracteres especiales del historial."""
    text = html.unescape(text)
    # Manejo de doble escape o entidades residuales
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    text = text.replace('&quot;', '"')
    text = text.replace('&apos;', "'")
    text = text.replace('&amp;', '&')
    return text


def get_history_file_path(project_path: str, filename: str) -> str:
    changes_dir = os.path.join(project_path, "_changes")
    if not os.path.exists(changes_dir):
        os.makedirs(changes_dir, exist_ok=True)
    
    safe_filename = filename.replace("/", "_").replace("\\", "_").replace(":", "")
    return os.path.join(changes_dir, f"_{safe_filename}.txt")


def _save_new_snapshot(project_path: str, filename: str, new_content: str) -> bool:
    """
    Añade una nueva 'snapshot' (versión completa) del archivo al final de su historial.
    """
    history_file = get_history_file_path(project_path, filename)
    try:
        with open(history_file, 'a', encoding='utf-8') as f:
            # Si el archivo no está vacío, añade un separador antes de la nueva versión.
            if f.tell() > 0:
                f.write(HISTORY_SEPARATOR)
            f.write(new_content)
    except IOError as e:
        print(f"Error al guardar snapshot: {e}")
        return False
    return True


def get_history_snapshots(project_path: str, filename: str) -> List[str]:
    """
    Obtiene todas las 'snapshots' (versiones completas) de un archivo desde su historial.
    """
    history_file = get_history_file_path(project_path, filename)
    if not os.path.exists(history_file):
        return []
    try:
        with open(history_file, 'r', encoding='utf-8') as f:
            content = f.read()
        # Devuelve una lista de strings, donde cada string es una versión completa del archivo.
        return content.split(HISTORY_SEPARATOR)
    except (IOError, FileNotFoundError):
        return []


def find_old_code_in_version(old_code: str, version_code: str) -> bool:
    """Verifica si old_code existe en el código de una versión, con flexibilidad."""
    if not old_code.strip() or not version_code:
        return False
    
    # 1. Búsqueda exacta (la más rápida y preferida)
    if old_code in version_code:
        return True

    # 2. Búsqueda con normalización de saltos de línea (Windows vs Unix)
    if old_code.replace('\n', '\r\n') in version_code:
        return True
    if old_code.replace('\r\n', '\n') in version_code:
        return True

    # 3. Búsqueda con regex ignorando espacios (como en change_parser)
    #    Esto es crucial para que la verificación y la aplicación sean consistentes.
    parts = old_code.strip().split()
    if not parts:
        return False
        
    try:
        # Escapamos caracteres especiales de regex y unimos con \s+
        # para que coincida con cualquier cantidad de espacios/saltos de línea.
        pattern = r'\s+'.join([re.escape(p) for p in parts])
        if re.search(pattern, version_code):
            return True
    except re.error:
        # Ignorar errores de regex si el input es extraño
        pass

    return False


def clear_apply_history(project_path: str, filename: str) -> bool:
    """Borra el historial de cambios de un archivo."""
    history_file = get_history_file_path(project_path, filename)
    
    if os.path.exists(history_file):
        os.remove(history_file)
    
    return True


def clear_all_apply_history(project_path: str) -> bool:
    """Borra todo el historial de cambios."""
    changes_dir = os.path.join(project_path, "_changes")
    
    if not os.path.exists(changes_dir):
        return True
    
    for filename in os.listdir(changes_dir):
        if filename.startswith("_") and filename.endswith(".txt"):
            filepath = os.path.join(changes_dir, filename)
            try:
                os.remove(filepath)
            except Exception:
                pass
    
    return True


def get_files_with_history(project_path: str) -> List[str]:
    """Obtiene lista de archivos que tienen historial."""
    changes_dir = os.path.join(project_path, "_changes")
    
    if not os.path.exists(changes_dir):
        return []
    
    files = []
    for filename in os.listdir(changes_dir):
        if filename.startswith("_") and filename.endswith(".txt") and filename != "_changes.txt":
            original_name = filename[1:-4]
            files.append(original_name)
    
    return files


def apply_change_with_history(project_path: str, change, original_code: str = None) -> Tuple[bool, str]:
    """
    Aplica un cambio considerando el historial de cambios.
    
    Args:
        project_path: Ruta del proyecto
        change: Objeto Change con old_code y new_code
        original_code: Código original del archivo (del último commit)
    
    Returns:
        (True, "") si se aplicó correctamente
        (False, mensaje_error) si falló
    """
    from core.change_parser import apply_change as core_apply_change
    
    # Obtener la ruta relativa para usarla como clave en el historial.
    rel_path = os.path.relpath(change.file_path, project_path)
    
    # Obtener todas las snapshots del historial.
    snapshots = get_history_snapshots(project_path, rel_path)
    
    print(f"[DEBUG apply_change_with_history] archivo={rel_path} accion={change.action} historial={len(snapshots)}")
    
    # Determinar sobre qué versión base vamos a trabajar.
    base_code = original_code
    if snapshots:
        # Si hay historial, la base es la última snapshot guardada.
        base_code = snapshots[-1]
    
    # Sincronizar el archivo en disco con nuestra versión base para una aplicación limpia.
    try:
        with open(change.file_path, 'w', encoding='utf-8') as f:
            f.write(base_code)
    except IOError as e:
        return False, f"No se pudo escribir en el archivo para aplicar el cambio: {e}"

    # Intentar aplicar el cambio usando el core_apply_change (que usa parches).
    print(f"[DEBUG] Intentando aplicar cambio sobre la versión base (Historial: {len(snapshots)})...")
    success = core_apply_change(change, project_path)
    
    if success:
        print("[DEBUG] ✓ Cambio aplicado con éxito.")
        # Leer el nuevo contenido del archivo tras el cambio.
        new_content = ""
        try:
            with open(change.file_path, 'r', encoding='utf-8') as f:
                new_content = f.read()
        except IOError:
            return False, "El cambio se aplicó pero no se pudo leer el resultado."
        
        # Guardar la nueva versión como una snapshot en el historial.
        _save_new_snapshot(project_path, rel_path, new_content)
        return True, ""
    else:
        print("[DEBUG] ✗ Falló la aplicación del cambio.")
        # Si falló, restaurar el archivo a como estaba antes del intento.
        try:
            with open(change.file_path, 'w', encoding='utf-8') as f:
                f.write(base_code)
        except IOError:
            pass # No mucho que hacer si la restauración también falla.
        
        # --- Lógica de Fallback: "Viaje en el Tiempo" ---
        # Si la aplicación falló, quizás el cambio era para una versión más antigua.
        # Buscamos hacia atrás en el historial.
        print("[DEBUG] Buscando en snapshots anteriores...")
        for i in range(len(snapshots) - 2, -1, -1):
            if find_old_code_in_version(change.old_code, snapshots[i]):
                print(f"[DEBUG] -> Código encontrado en snapshot #{i}. Esto invalidará cambios posteriores.")
                # Encontramos una versión antigua que contiene el código.
                # Revertimos el archivo a esa versión y aplicamos el cambio.
                # ADVERTENCIA: Esto descarta los cambios que se hicieron después de esa snapshot.
                with open(change.file_path, 'w', encoding='utf-8') as f:
                    f.write(snapshots[i])
                
                success_retry = core_apply_change(change, project_path)
                if success_retry:
                    new_content = ""
                    with open(change.file_path, 'r', encoding='utf-8') as f:
                        new_content = f.read()
                    
                    # Borramos el historial posterior al punto de bifurcación.
                    clear_apply_history(project_path, rel_path)
                    for j in range(i + 1):
                        _save_new_snapshot(project_path, rel_path, snapshots[j])
                    _save_new_snapshot(project_path, rel_path, new_content)
                    
                    print("[DEBUG] ✓ Cambio aplicado en una versión anterior del historial.")
                    return True, ""

        # Si no se encontró en ninguna parte, restauramos y fallamos.
        with open(change.file_path, 'w', encoding='utf-8') as f:
            f.write(base_code)
        return False, "El código a modificar no se encontró en la versión actual ni en el historial."


def clear_history_for_files(project_path: str, files: List[str]) -> None:
    """Borra el historial de cambios para una lista de archivos."""
    for filepath in files:
        rel_path = os.path.relpath(filepath, project_path)
        clear_apply_history(project_path, rel_path)
