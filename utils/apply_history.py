import os
import re
import html
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from utils.git_manager import apply_patch_to_text


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


def save_change(project_path: str, filename: str, old_code: str, new_code: str, action: str = "reemplazar") -> bool:
    """Guarda un cambio individual (old_code y new_code) en el historial."""
    if old_code == new_code:
        return True
    
    history_file = get_history_file_path(project_path, filename)
    
    changes = []
    
    if os.path.exists(history_file):
        try:
            tree = ET.parse(history_file)
            root = tree.getroot()
            for change_elem in root.findall("change"):
                date = change_elem.find("date")
                old = change_elem.find("old_code")
                new = change_elem.find("new_code")
                act = change_elem.find("action")
                if date is not None and old is not None and new is not None:
                    changes.append({
                        "date": date.text or "",
                        "old_code": old.text or "",
                        "new_code": new.text or "",
                        "action": act.text if act is not None else "reemplazar"
                    })
        except Exception:
            changes = []
    
    new_change = {
        "date": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "old_code": old_code,
        "new_code": new_code,
        "action": action
    }
    changes.append(new_change)
    
    root = ET.Element("history")
    for change in changes:
        change_elem = ET.SubElement(root, "change")
        date_elem = ET.SubElement(change_elem, "date")
        date_elem.text = change["date"]
        old_elem = ET.SubElement(change_elem, "old_code")
        old_elem.text = change["old_code"]
        new_elem = ET.SubElement(change_elem, "new_code")
        new_elem.text = change["new_code"]
        act_elem = ET.SubElement(change_elem, "action")
        act_elem.text = change.get("action", "reemplazar")
    
    tree = ET.ElementTree(root)
    tree.write(history_file, encoding="utf-8", xml_declaration=True)
    
    return True


def get_apply_history(project_path: str, filename: str) -> List[Dict[str, str]]:
    """Obtiene el historial de cambios (old_code y new_code)."""
    history_file = get_history_file_path(project_path, filename)
    
    if not os.path.exists(history_file):
        return []
    
    changes = []
    
    try:
        tree = ET.parse(history_file)
        root = tree.getroot()
        for change_elem in root.findall("change"):
            date = change_elem.find("date")
            old = change_elem.find("old_code")
            new = change_elem.find("new_code")
            act = change_elem.find("action")
            if date is not None and old is not None and new is not None:
                changes.append({
                    "date": date.text or "",
                    "old_code": normalize_history_text(old.text or ""),
                    "new_code": normalize_history_text(new.text or ""),
                    "action": act.text if act is not None else "reemplazar"
                })
    except Exception:
        return []
    
    return changes


def rebuild_version(original_code: str, changes: List[Dict[str, str]]) -> str:
    """
    Reconstruye una versión del código aplicando cambios secuenciales.
    
    Args:
        original_code: Código base del último commit de git
        changes: Lista de cambios {old_code, new_code} en orden
    
    Returns:
        Código reconstruido después de aplicar todos los cambios
    """
    if not changes:
        return original_code
    
    result = original_code
    
    for change in changes:
        old_code = change.get("old_code", "")
        new_code = change.get("new_code", "")
        action = change.get("action", "reemplazar")
        
        if action in ['patch', 'parche']:
            result = apply_patch_to_text(result, new_code)
            continue
        
        if not old_code:
            continue
        
        # Búsqueda exacta. No usamos strip() para respetar la indentación.
        if old_code in result:
            result = result.replace(old_code, new_code, 1)
    
    return result


def rebuild_version_to_index(original_code: str, changes: List[Dict[str, str]], to_index: int) -> str:
    """
    Reconstruye una versión del código hasta un índice específico.
    
    Args:
        original_code: Código base del último commit de git
        changes: Lista de cambios {old_code, new_code} en orden
        to_index: Índice hasta el cual reconstruir (inclusive)
    
    Returns:
        Código reconstruido después de aplicar cambios[0..to_index]
    """
    if not changes or to_index < 0:
        return original_code
    
    result = original_code
    limit = min(to_index + 1, len(changes))
    
    for i in range(limit):
        change = changes[i]
        old_code = change.get("old_code", "")
        new_code = change.get("new_code", "")
        action = change.get("action", "reemplazar")
        
        if action in ['patch', 'parche']:
            result = apply_patch_to_text(result, new_code)
            continue
        
        if not old_code:
            continue
        
        # Búsqueda exacta sin strip() para mantener consistencia.
        if old_code in result:
            result = result.replace(old_code, new_code, 1)
    
    return result


def rebuild_version_from_index(original_code: str, changes: List[Dict[str, str]], from_index: int) -> str:
    """
    Reconstruye una versión del código desde un índice específico.
    
    Args:
        original_code: Código base del último commit de git
        changes: Lista de cambios {old_code, new_code} en orden
        from_index: Índice desde el cual reconstruir
    
    Returns:
        Código reconstruido después de aplicar cambios[from_index..]
    """
    if not changes or from_index >= len(changes):
        return original_code
    
    current_version = rebuild_version_to_index(original_code, changes, from_index - 1) if from_index > 0 else original_code
    
    for i in range(from_index, len(changes)):
        change = changes[i]
        old_code = change.get("old_code", "")
        new_code = change.get("new_code", "")
        
        if not old_code:
            continue
        
        if old_code in current_version:
            current_version = current_version.replace(old_code, new_code, 1)
    
    return current_version


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
    
    rel_path = os.path.relpath(change.file_path, project_path)
    changes = get_apply_history(project_path, rel_path)
    
    current_file_code = ""
    if os.path.exists(change.file_path):
        try:
            with open(change.file_path, 'r', encoding='utf-8') as f:
                current_file_code = f.read()
        except:
            pass
    
    if original_code is None:
        original_code = current_file_code
    
    if not changes:
        print(f"[DEBUG] Sin historial previo para '{rel_path}'.")
        
        # Caso especial para PATCH: No tiene old_code, intentamos aplicar directamente
        if change.action in ['patch', 'parche']:
            print(f"[DEBUG] Aplicando modo PATCH (git apply)...")
            success = core_apply_change(change, project_path)
            if success:
                save_change(project_path, rel_path, change.old_code, change.new_code, change.action)
                print(f"[DEBUG] ✓ Parche aplicado sobre versión actual.")
                return True, ""
            
            print(f"[DEBUG] ✗ Parche falló en local. Intentando sobre HEAD...")
            
            # Restaurar desde HEAD para intentar aplicar el parche en limpio
            parent_dir = os.path.dirname(change.file_path)
            if parent_dir and not os.path.exists(parent_dir):
                os.makedirs(parent_dir, exist_ok=True)
                
            with open(change.file_path, 'w', encoding='utf-8') as f:
                f.write(original_code)
            
            success = core_apply_change(change, project_path)
            
            if success:
                save_change(project_path, rel_path, change.old_code, change.new_code, change.action)
                print(f"[DEBUG] ✓ Parche aplicado sobre HEAD.")
                return True, ""
            
            print(f"[DEBUG] ✗ Parche falló también sobre HEAD. Restaurando contenido usuario.")
            if current_file_code:
                with open(change.file_path, 'w', encoding='utf-8') as f:
                    f.write(current_file_code)
            return False, "El parche no se pudo aplicar (git apply falló). Revisa la consola para ver el error de git."

        stripped_old = change.old_code.strip()
        if not stripped_old:
            print(f"[DEBUG] ⚠️ El código antiguo es inválido (vacío o solo espacios). Se aborta la búsqueda.")
            print(f"[DEBUG] Raw: {repr(change.old_code)}")
            return False, "El código a reemplazar está vacío o contiene solo espacios."

        # 1. Intentar aplicar sobre el archivo actual (preservando cambios locales del usuario)
        # Esto es lo preferible si la IA generó el código basándose en el estado actual del archivo
        if stripped_old in current_file_code:
            print(f"[DEBUG] -> El código existe en el archivo actual. Aplicando directamente...")
            success = core_apply_change(change, project_path)
            
            if success:
                save_change(project_path, rel_path, change.old_code, change.new_code, change.action)
                print(f"[DEBUG] ✓ Cambio aplicado sobre la versión actual del usuario.")
                return True, ""
            else:
                print(f"[DEBUG] -> Falló la aplicación directa.")
        else:
             print(f"[DEBUG] -> El código NO se encontró en el archivo actual.")

        # 2. Si falla lo anterior, restaurar desde HEAD (comportamiento fallback)
        print(f"[DEBUG] Intentando restaurar desde git HEAD para aplicar...")
        
        parent_dir = os.path.dirname(change.file_path)
        if parent_dir and not os.path.exists(parent_dir):
            os.makedirs(parent_dir, exist_ok=True)
            
        with open(change.file_path, 'w', encoding='utf-8') as f:
            f.write(original_code)
        
        success = core_apply_change(change, project_path)
        
        if success:
            save_change(project_path, rel_path, change.old_code, change.new_code, change.action)
            print(f"[DEBUG] ✓ Cambio aplicado exitosamente a la versión de HEAD.")
            return True, ""
        
        print(f"[DEBUG] ✗ Falló también sobre HEAD. Restaurando contenido usuario.")
        if current_file_code:
            with open(change.file_path, 'w', encoding='utf-8') as f:
                f.write(current_file_code)

        return False, "El cambio no se pudo aplicar ni en la versión actual ni en la versión original (git)."

    last_version_code = rebuild_version(original_code, changes)
    
    print(f"[DEBUG apply_change_with_history] archivo={rel_path} accion={change.action} historial={len(changes)}")
    
    if not change.old_code:
        success = core_apply_change(change, project_path)
        if success:
            save_change(project_path, rel_path, "", change.new_code, change.action)
        return success, ""
    
    # Si es un parche, no intentamos hacer "Time Travel" complejo, confiamos en git apply
    if change.action in ['patch', 'parche']:
        success = core_apply_change(change, project_path)
        if success:
            save_change(project_path, rel_path, change.old_code, change.new_code, change.action)
            return True, ""
        return False, "Falló la aplicación del parche"

    print(f"[DEBUG] Verificando si old_code existe en last_version_code...")
    if find_old_code_in_version(change.old_code, last_version_code):
        print(f"[DEBUG] -> Encontrado en last_version_code. Aplicando...")
        success = core_apply_change(change, project_path)
        if success:
            save_change(project_path, rel_path, change.old_code, change.new_code, change.action)
            return True, ""
        else:
            print(f"[DEBUG] -> Falló la aplicación en el archivo físico. Intentando sincronizar archivo con historial...")
            # Si el historial dice que tenemos el código, pero el archivo físico no,
            # significa que el archivo físico está desincronizado (posiblemente editado externamente o corrupto por saltos de linea).
            # Forzamos que el archivo físico sea igual a last_version_code.
            with open(change.file_path, 'w', encoding='utf-8') as f:
                f.write(last_version_code)
            
            success_retry = core_apply_change(change, project_path)
            if success_retry:
                save_change(project_path, rel_path, change.old_code, change.new_code, change.action)
                print(f"[DEBUG] ✓ Cambio aplicado tras sincronizar archivo con historial.")
                return True, ""
            else:
                print(f"[DEBUG] ✗ Falló incluso tras forzar la versión del historial.")
                # Restauramos backup por seguridad si es necesario, aunque aquí last_version_code es la "verdad" del sistema
                return False, "Error de sincronización: El historial contiene el código pero no se pudo aplicar al archivo."
    
    print(f"[DEBUG] No encontrado en last_version_code. Buscando en historial histórico...")
    for i, ch in enumerate(changes):
        version_at_i = rebuild_version_to_index(original_code, changes, i)
        found = find_old_code_in_version(change.old_code, version_at_i)
        
        if found:
            backup_code = last_version_code
            reverted_code = rebuild_version_to_index(original_code, changes, i - 1) if i > 0 else original_code
            with open(change.file_path, 'w', encoding='utf-8') as f:
                f.write(reverted_code)
            
            success = core_apply_change(change, project_path)
            
            if not success:
                with open(change.file_path, 'w', encoding='utf-8') as f:
                    f.write(backup_code)
                return False, "Error al aplicar el cambio de IA."
            
            save_change(project_path, rel_path, change.old_code, change.new_code, change.action)
            
            return True, ""
    
    # FALLBACK: Buscar en TODAS las versiones reconstruidas del historial
    print(f"[DEBUG] === FALLBACK DEBUG ===")
    print(f"[DEBUG] Cambios en historial: {len(changes)}")
    print(f"[DEBUG] old_code a buscar (primeros 100 chars):")
    print(repr(change.old_code[:100]))
    
    # Mostrar los cambios del historial
    for idx, ch in enumerate(changes):
        print(f"[DEBUG] Historial #{idx}:")
        print(f"[DEBUG]   old_code (primeros 80): {repr(ch.get('old_code', '')[:80])}")
        print(f"[DEBUG]   new_code (primeros 80): {repr(ch.get('new_code', '')[:80])}")
    
    # Buscar en cada versión reconstruida (desde la más reciente hasta la original)
    found_in_version_index = None
    for i in range(len(changes) - 1, -1, -1):
        version_at_i = rebuild_version_to_index(original_code, changes, i)
        contains = find_old_code_in_version(change.old_code, version_at_i)
        print(f"[DEBUG] Versión {i} contiene código: {contains}")
        if contains:
            found_in_version_index = i
            print(f"[DEBUG] Código encontrado en versión {i}")
            break
    
    if found_in_version_index is not None:
        # Encontrar cuál cambio modificó este código
        conflicting_change_index = None
        for i in range(found_in_version_index, len(changes)):
            ch = changes[i]
            if find_old_code_in_version(change.old_code, ch.get("new_code", "")):
                conflicting_change_index = i
                break
        
        if conflicting_change_index is not None:
            # Revertir al estado justo antes del cambio conflictivo
            reverted_code = rebuild_version_to_index(original_code, changes, conflicting_change_index - 1) if conflicting_change_index > 0 else original_code
            with open(change.file_path, 'w', encoding='utf-8') as f:
                f.write(reverted_code)
            
            success = core_apply_change(change, project_path)
            
            if not success:
                with open(change.file_path, 'w', encoding='utf-8') as f:
                    f.write(last_version_code)
                return False, "Error al aplicar el cambio después de revertir."
            
            save_change(project_path, rel_path, change.old_code, change.new_code, change.action)
            print(f"[DEBUG] ✓ Cambio aplicado (FALLBACK exitoso)")
            return True, ""
    
    # Si no se encontró en ninguna versión, buscar en git HEAD original
    print(f"[DEBUG] Verificando en original_code (Git HEAD)...")
    if find_old_code_in_version(change.old_code, original_code):
        print(f"[DEBUG] -> Encontrado en original_code.")
        if change.old_code.strip() in current_file_code:
            print(f"[DEBUG] -> También está en el archivo actual en disco. Aplicando directo...")
            success = core_apply_change(change, project_path)
            if success:
                save_change(project_path, rel_path, change.old_code, change.new_code, change.action)
                return True, ""
        
        print(f"[DEBUG] -> No está en archivo actual. Restaurando a original_code y aplicando...")
        with open(change.file_path, 'w', encoding='utf-8') as f:
            f.write(original_code)
        
        success = core_apply_change(change, project_path)
        
        if success:
            for ch in changes:
                save_change(project_path, rel_path, ch.get("old_code", ""), ch.get("new_code", ""), ch.get("action", "reemplazar"))
            save_change(project_path, rel_path, change.old_code, change.new_code, change.action)
            return True, ""
        else:
            print(f"[DEBUG] -> Falló core_apply_change sobre original_code.")
    
    print(f"[DEBUG] ✗ ERROR: Código no encontrado en ninguna versión")
    return False, "El código no existe en el archivo actual ni en el historial."


def clear_history_for_files(project_path: str, files: List[str]) -> None:
    """Borra el historial de cambios para una lista de archivos."""
    for filepath in files:
        rel_path = os.path.relpath(filepath, project_path)
        clear_apply_history(project_path, rel_path)
