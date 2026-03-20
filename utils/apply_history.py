import os
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import List, Dict, Optional, Tuple


def get_history_file_path(project_path: str, filename: str) -> str:
    changes_dir = os.path.join(project_path, "_changes")
    if not os.path.exists(changes_dir):
        os.makedirs(changes_dir, exist_ok=True)
    
    safe_filename = filename.replace("/", "_").replace("\\", "_").replace(":", "")
    return os.path.join(changes_dir, f"_{safe_filename}.txt")


def save_change(project_path: str, filename: str, old_code: str, new_code: str) -> bool:
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
                if date is not None and old is not None and new is not None:
                    changes.append({
                        "date": date.text or "",
                        "old_code": old.text or "",
                        "new_code": new.text or ""
                    })
        except Exception:
            changes = []
    
    new_change = {
        "date": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "old_code": old_code,
        "new_code": new_code
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
            if date is not None and old is not None and new is not None:
                changes.append({
                    "date": date.text or "",
                    "old_code": old.text or "",
                    "new_code": new.text or ""
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
        
        if not old_code:
            continue
        
        old_stripped = old_code.strip()
        
        if old_stripped in result:
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
        
        if not old_code:
            continue
        
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
    """Verifica si old_code existe en el código de una versión."""
    if not old_code or not version_code:
        return False
    
    old_stripped = old_code.strip()
    version_stripped = version_code.strip()
    
    return old_stripped in version_stripped


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
    
    last_version_code = rebuild_version(original_code, changes)
    
    print(f"[DEBUG apply_change_with_history] ===")
    print(f"[DEBUG] archivo: {rel_path}")
    print(f"[DEBUG] action: {change.action}")
    print(f"[DEBUG] tiene old_code: {bool(change.old_code)}")
    print(f"[DEBUG] old_code length: {len(change.old_code) if change.old_code else 0}")
    print(f"[DEBUG] historial de cambios: {len(changes)}")
    
    if not change.old_code:
        success = core_apply_change(change)
        if success:
            save_change(project_path, rel_path, "", change.new_code)
        return success, ""
    
    print(f"[DEBUG] === Verificando old_code en última versión ===")
    print(f"[DEBUG] old_code (primeros 150 chars): {repr(change.old_code[:150])}")
    print(f"[DEBUG] old_code.strip() (primeros 150): {repr(change.old_code.strip()[:150])}")
    print(f"[DEBUG] last_version_code length: {len(last_version_code)}")
    print(f"[DEBUG] last_version_code (primeros 200 chars): {repr(last_version_code[:200])}")
    print(f"[DEBUG] find_old_code_in_version resultado: {find_old_code_in_version(change.old_code, last_version_code)}")
    
    if find_old_code_in_version(change.old_code, last_version_code):
        print(f"[DEBUG] ✓ Código encontrado en última versión, aplicando...")
        success = core_apply_change(change)
        if success:
            save_change(project_path, rel_path, change.old_code, change.new_code)
        return success, ""
    
    print(f"[DEBUG] ✗ Código NO encontrado en última versión, buscando en historial...")
    print(f"[DEBUG] Cambios en historial: {len(changes)}")
    
    for i, ch in enumerate(changes):
        version_at_i = rebuild_version_to_index(original_code, changes, i)
        print(f"[DEBUG] Verificando historial #{i}: {repr(ch.get('date', 'N/A'))}")
        print(f"[DEBUG] version_at_i length: {len(version_at_i)}")
        print(f"[DEBUG] version_at_i (primeros 150): {repr(version_at_i[:150])}")
        found = find_old_code_in_version(change.old_code, version_at_i)
        print(f"[DEBUG] find_old_code_in_version result: {found}")
        
        if found:
            backup_code = last_version_code
            
            reverted_code = rebuild_version_to_index(original_code, changes, i - 1) if i > 0 else original_code
            
            with open(change.file_path, 'w', encoding='utf-8') as f:
                f.write(reverted_code)
            
            success = core_apply_change(change)
            
            if not success:
                with open(change.file_path, 'w', encoding='utf-8') as f:
                    f.write(backup_code)
                return False, "Error al aplicar el cambio de IA."
            
            save_change(project_path, rel_path, change.old_code, change.new_code)
            
            return True, ""
    
    # FALLBACK: Buscar en original_code (git HEAD) si no se encuentra en historial
    print(f"[DEBUG] === FALLBACK: Buscando en original_code (git HEAD) ===")
    print(f"[DEBUG] original_code length: {len(original_code)}")
    
    if find_old_code_in_version(change.old_code, original_code):
        print(f"[DEBUG] ✓ old_code encontrado en original_code")
        
        # Encontrar cuál fue el último cambio que modificó este código
        conflicting_change_index = None
        for i, ch in enumerate(changes):
            if find_old_code_in_version(change.old_code, ch.get("new_code", "")):
                conflicting_change_index = i
                print(f"[DEBUG] Código fue modificado por cambio #{i}: {repr(ch.get('date', 'N/A'))}")
                break
        
        if conflicting_change_index is not None:
            # Revertir al estado anterior al cambio conflictivo
            reverted_code = rebuild_version_to_index(original_code, changes, conflicting_change_index - 1) if conflicting_change_index > 0 else original_code
            print(f"[DEBUG] Revirtiendo archivo a versión antes del cambio conflictivo...")
            print(f"[DEBUG] reverted_code length: {len(reverted_code)}")
            
            with open(change.file_path, 'w', encoding='utf-8') as f:
                f.write(reverted_code)
            
            # Ahora aplicar el nuevo cambio
            success = core_apply_change(change)
            
            if not success:
                # Restaurar el último estado conocido
                with open(change.file_path, 'w', encoding='utf-8') as f:
                    f.write(last_version_code)
                return False, "Error al aplicar el cambio después de revertir."
            
            save_change(project_path, rel_path, change.old_code, change.new_code)
            print(f"[DEBUG] ✓ Cambio aplicado exitosamente después de revertir")
            return True, ""
        else:
            # El código existe en original pero no fue modificado - buscar en archivo actual
            print(f"[DEBUG] Código existe en original pero no debería estar modificado")
            print(f"[DEBUG] Intentando aplicar cambio directamente al archivo actual...")
            
            # Verificar si el código actual del archivo contiene el old_code
            if change.old_code.strip() in current_file_code:
                success = core_apply_change(change)
                if success:
                    save_change(project_path, rel_path, change.old_code, change.new_code)
                    return True, ""
            
            # Revertir todos los cambios y aplicar el nuevo
            print(f"[DEBUG] Revirtiendo todos los cambios ({len(changes)})...")
            with open(change.file_path, 'w', encoding='utf-8') as f:
                f.write(original_code)
            
            success = core_apply_change(change)
            
            if success:
                for ch in changes:
                    save_change(project_path, rel_path, ch.get("old_code", ""), ch.get("new_code", ""))
                save_change(project_path, rel_path, change.old_code, change.new_code)
                return True, ""
            else:
                # Restaurar estado
                with open(change.file_path, 'w', encoding='utf-8') as f:
                    f.write(last_version_code)
                return False, "Error al aplicar el cambio."
    
    print(f"[DEBUG] ✗ ERROR: Código no encontrado en ninguna versión")
    print(f"[DEBUG] Buscando: {repr(change.old_code[:100])}...")
    return False, f"El código no existe en el archivo actual ni en el historial.\n\nold_code length: {len(change.old_code)}\nlast_version length: {len(last_version_code)}\noriginal_code length: {len(original_code)}"


def clear_history_for_files(project_path: str, files: List[str]) -> None:
    """Borra el historial de cambios para una lista de archivos."""
    for filepath in files:
        rel_path = os.path.relpath(filepath, project_path)
        clear_apply_history(project_path, rel_path)
