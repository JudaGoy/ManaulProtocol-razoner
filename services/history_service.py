import os
import re
import html
from typing import List, Tuple
from services.git_service import apply_patch_to_text


HISTORY_SEPARATOR = "\n---_APPLY_HISTORY_VERSION_SEPARATOR_---\n"


def normalize_history_text(text: str) -> str:
    text = html.unescape(text)
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
    history_file = get_history_file_path(project_path, filename)
    try:
        with open(history_file, 'a', encoding='utf-8') as f:
            if f.tell() > 0:
                f.write(HISTORY_SEPARATOR)
            f.write(new_content)
    except IOError as e:
        print(f"Error al guardar snapshot: {e}")
        return False
    return True


def get_history_snapshots(project_path: str, filename: str) -> List[str]:
    history_file = get_history_file_path(project_path, filename)
    if not os.path.exists(history_file):
        return []
    try:
        with open(history_file, 'r', encoding='utf-8') as f:
            content = f.read()
        return content.split(HISTORY_SEPARATOR)
    except (IOError, FileNotFoundError):
        return []


def find_old_code_in_version(old_code: str, version_code: str) -> bool:
    if not old_code.strip() or not version_code:
        return False
    
    if old_code in version_code:
        return True

    if old_code.replace('\n', '\r\n') in version_code:
        return True
    if old_code.replace('\r\n', '\n') in version_code:
        return True

    parts = old_code.strip().split()
    if not parts:
        return False
        
    try:
        pattern = r'\s+'.join([re.escape(p) for p in parts])
        if re.search(pattern, version_code):
            return True
    except re.error:
        pass

    return False


def clear_apply_history(project_path: str, filename: str) -> bool:
    history_file = get_history_file_path(project_path, filename)
    
    if os.path.exists(history_file):
        os.remove(history_file)
    
    return True


def clear_all_apply_history(project_path: str) -> bool:
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
    from domain.models import apply_change as domain_apply_change
    
    rel_path = os.path.relpath(change.file_path, project_path)
    snapshots = get_history_snapshots(project_path, rel_path)
    
    print(f"[DEBUG apply_change_with_history] archivo={rel_path} accion={change.action} historial={len(snapshots)}")
    
    base_code = original_code
    if snapshots:
        base_code = snapshots[-1]
    
    try:
        with open(change.file_path, 'w', encoding='utf-8') as f:
            f.write(base_code)
    except IOError as e:
        return False, f"No se pudo escribir en el archivo para aplicar el cambio: {e}"

    print(f"[DEBUG] Intentando aplicar cambio sobre la versión base (Historial: {len(snapshots)})...")
    success = domain_apply_change(change, project_path)
    
    if success:
        print("[DEBUG] ✓ Cambio aplicado con éxito.")
        new_content = ""
        try:
            with open(change.file_path, 'r', encoding='utf-8') as f:
                new_content = f.read()
        except IOError:
            return False, "El cambio se aplicó pero no se pudo leer el resultado."
        
        _save_new_snapshot(project_path, rel_path, new_content)
        return True, ""
    else:
        print("[DEBUG] ✗ Falló la aplicación del cambio.")
        try:
            with open(change.file_path, 'w', encoding='utf-8') as f:
                f.write(base_code)
        except IOError:
            pass
        
        print("[DEBUG] Buscando en snapshots anteriores...")
        for i in range(len(snapshots) - 2, -1, -1):
            if find_old_code_in_version(change.old_code, snapshots[i]):
                print(f"[DEBUG] -> Código encontrado en snapshot #{i}. Esto invalidará cambios posteriores.")
                with open(change.file_path, 'w', encoding='utf-8') as f:
                    f.write(snapshots[i])
                
                success_retry = domain_apply_change(change, project_path)
                if success_retry:
                    new_content = ""
                    with open(change.file_path, 'r', encoding='utf-8') as f:
                        new_content = f.read()
                    
                    clear_apply_history(project_path, rel_path)
                    for j in range(i + 1):
                        _save_new_snapshot(project_path, rel_path, snapshots[j])
                    _save_new_snapshot(project_path, rel_path, new_content)
                    
                    print("[DEBUG] ✓ Cambio aplicado en una versión anterior del historial.")
                    return True, ""

        with open(change.file_path, 'w', encoding='utf-8') as f:
            f.write(base_code)
        return False, "El código a modificar no se encontró en la versión actual ni en el historial."


def clear_history_for_files(project_path: str, files: List[str]) -> None:
    for filepath in files:
        rel_path = os.path.relpath(filepath, project_path)
        clear_apply_history(project_path, rel_path)
