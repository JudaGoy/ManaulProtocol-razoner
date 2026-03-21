import os
import re
import html
import difflib
from dataclasses import dataclass
from typing import List, Tuple


def normalize_text(text: str) -> str:
    text = html.unescape(text)
    
    replacements = {
        '├│': '│',
        '├': '',
        'Â': '',
        'â€™': "'",
        'â€œ': '"',
        'â€': '"',
        'â€"': '—',
        'â€"': '–',
        'Ã': 'Á',
        'Ã': 'É',
        'Ã': 'Í',
        'Ã': 'Ó',
        'Ã': 'Ú',
        'Ã±': 'ñ',
        'Ã': 'á',
        'Ã©': 'é',
        'Ã­': 'í',
        'Ã³': 'ó',
        'Ãº': 'ú',
    }
    
    for wrong, correct in replacements.items():
        text = text.replace(wrong, correct)
    
    text = re.sub(r'&lt;', '<', text)
    text = re.sub(r'&gt;', '>', text)
    text = re.sub(r'&amp;', '&', text)
    text = re.sub(r'&quot;', '"', text)
    text = re.sub(r'&apos;', "'", text)
    
    return text


@dataclass
class Change:
    file_path: str
    action: str
    old_code: str
    new_code: str
    instances: str = "all"
    raw_xml: str = ""
    applied: bool = False


@dataclass  
class ChangeError:
    error_type: str
    message: str
    file_path: str
    detail: str


def replace_specific_instances(content: str, old_code: str, new_code: str, instances: str) -> str:
    if instances == "all" or not instances:
        return content.replace(old_code, new_code)
    
    positions = []
    start = 0
    while True:
        pos = content.find(old_code, start)
        if pos == -1:
            break
        positions.append(pos)
        start = pos + 1
    
    if not positions:
        return content
    
    try:
        target = [int(i.strip()) for i in instances.split(",")]
    except ValueError:
        return content.replace(old_code, new_code)
    
    result = content
    for idx in sorted(target, reverse=True):
        if 0 <= idx < len(positions):
            pos = positions[idx]
            result = result[:pos] + new_code + result[pos + len(old_code):]
    
    return result


def parse_changes(changes_path, project_path):
    changes = []
    errors = []
    
    if not os.path.exists(changes_path):
        return changes, errors
    
    for filename in os.listdir(changes_path):
        if filename.endswith('.txt'):
            filepath = os.path.join(changes_path, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                file_changes, file_errors = parse_xml_content(content, project_path)
                changes.extend(file_changes)
                errors.extend(file_errors)
                
            except Exception as e:
                errors.append(ChangeError(
                    error_type="archivo_invalido",
                    message=f"Error al leer {filename}",
                    file_path=filename,
                    detail=str(e)
                ))
    
    return changes, errors


def parse_xml_content(content, project_path):
    changes = []
    errors = []
    
    content = re.sub(r'<system-reminder>.*?</system-reminder>', '', content, flags=re.DOTALL | re.IGNORECASE)
    content = re.sub(r'<system-.*?>.*?</system-.*?>', '', content, flags=re.DOTALL)
    
    block_pattern = re.compile(r'<CAMBIOS>(.*?)</CAMBIOS>', re.DOTALL)
    blocks = block_pattern.findall(content)
    
    for block in blocks:
        archivo_match = re.search(r'<ARCHIVO>\s*(.+?)\s*</ARCHIVO>', block, re.DOTALL)
        if not archivo_match:
            continue
        
        accion_match = re.search(r'<ACCION>\s*(.+?)\s*</ACCION>', block, re.DOTALL)
        old_match = re.search(r'<CODIGO_ANTIGUO>\s*(.*?)\s*</CODIGO_ANTIGUO>', block, re.DOTALL)
        new_match = re.search(r'<CODIGO_NUEVO>\s*(.*?)\s*</CODIGO_NUEVO>', block, re.DOTALL)
        
        if not new_match:
            continue
        
        new_code = new_match.group(1)
        old_code = old_match.group(1) if old_match else ""
        archivo = archivo_match.group(1).strip()
        accion = accion_match.group(1).strip().lower() if accion_match else ''
        
        if not accion and ('diff --git' in new_code or ('--- a/' in new_code and '+++ b/' in new_code)):
            accion = 'patch'
        
        instances_match = re.search(r'<INSTANCIAS>\s*(.*?)\s*</INSTANCIAS>', block, re.DOTALL)
        instances = instances_match.group(1).strip() if instances_match else "all"
        
        if archivo:
            abs_path = os.path.join(project_path, archivo)
            normalized_old = normalize_text(old_code)
            normalized_new = normalize_text(new_code)
            
            changes.append(Change(
                file_path=abs_path,
                action=accion,
                old_code=normalized_old,
                new_code=normalized_new,
                instances=instances,
                raw_xml=f"<CAMBIOS>{block}</CAMBIOS>"
            ))
    
    return changes, errors


def apply_change(change: Change, project_path: str = None) -> bool:
    try:
        from services.git_service import apply_git_patch
        
        if change.action == 'patch' or change.action == 'parche':
            if not project_path:
                print("[ERROR] Se requiere project_path para aplicar parches")
                return False
            
            success, msg = apply_git_patch(project_path, change.new_code)
            if not success:
                print(f"[DEBUG] ✗ git apply falló:\n{msg}")
            change.applied = success
            return success

        if change.action in ['reemplazar', 'insertar']:
            return _apply_text_change_as_patch(change, project_path)

        if change.action == 'crear_carpeta':
            os.makedirs(change.file_path, exist_ok=True)
            change.applied = True
            return True
        
        if change.action == 'eliminar_carpeta':
            if os.path.exists(change.file_path) and os.path.isdir(change.file_path):
                import shutil
                shutil.rmtree(change.file_path)
                change.applied = True
                return True
            return False
        
        if change.action == 'eliminar_archivo':
            if os.path.exists(change.file_path) and os.path.isfile(change.file_path):
                os.remove(change.file_path)
                change.applied = True
                return True
            return False
        
        if change.action == 'crear':
            parent_dir = os.path.dirname(change.file_path)
            if parent_dir and not os.path.exists(parent_dir):
                os.makedirs(parent_dir, exist_ok=True)
            with open(change.file_path, 'w', encoding='utf-8') as f:
                f.write(change.new_code)
            change.applied = True
            return True
        
        return False
        
    except Exception as e:
        print(f"[DEBUG] Excepción: {type(e).__name__}: {e}")
        return False


def _apply_text_change_as_patch(change: Change, project_path: str) -> bool:
    from services.git_service import apply_git_patch
    
    if not project_path:
        print(f"[ERROR] Se requiere project_path para aplicar '{change.action}' como parche.")
        return False
    if not os.path.exists(change.file_path):
        print(f"[DEBUG] ✗ ERROR: Archivo no encontrado para '{change.action}': {change.file_path}")
        return False

    print(f"[DEBUG apply_change] Procesando {change.action.upper()} como PATCH para {os.path.basename(change.file_path)}")
    
    with open(change.file_path, 'r', encoding='utf-8') as f:
        original_content = f.read()

    target_old_code = change.old_code
    
    if not target_old_code.strip():
        print(f"[DEBUG] ⚠️ RECHAZADO: El código a buscar ('old_code') está vacío o solo contiene espacios.")
        return False

    if target_old_code not in original_content:
        print(f"[DEBUG] No hay coincidencia exacta. Intentando búsqueda flexible...")
        
        if target_old_code.replace('\n', '\r\n') in original_content:
            target_old_code = target_old_code.replace('\n', '\r\n')
            print(f"[DEBUG] -> Coincidencia encontrada ajustando saltos de línea (LF -> CRLF).")
        elif target_old_code.replace('\r\n', '\n') in original_content:
            target_old_code = target_old_code.replace('\r\n', '\n')
            print(f"[DEBUG] -> Coincidencia encontrada ajustando saltos de línea (CRLF -> LF).")
        else:
            parts = change.old_code.split()
            if parts:
                pattern = r'\s+'.join([re.escape(p) for p in parts])
                match = re.search(pattern, original_content)
                if match:
                    target_old_code = match.group(0)
                    print(f"[DEBUG] -> Coincidencia encontrada ignorando diferencias de espacios/indentación.")
                else:
                    print(f"[DEBUG] ✗ ERROR: Código no encontrado ni con búsqueda flexible.")
                    return False
            else:
                return False

    if change.action == 'reemplazar':
        new_content = replace_specific_instances(original_content, target_old_code, change.new_code, change.instances)
    elif change.action == 'insertar':
        new_content = original_content.replace(target_old_code, target_old_code + "\n" + change.new_code, 1)
    else:
        return False

    if original_content == new_content:
        print("[DEBUG] ! AVISO: La operación no resultó en cambios. Se considera exitoso.")
        change.applied = True
        return True

    rel_path = os.path.relpath(change.file_path, project_path).replace('\\', '/')
    
    diff = difflib.unified_diff(
        original_content.splitlines(keepends=True),
        new_content.splitlines(keepends=True),
        fromfile=f'a/{rel_path}',
        tofile=f'b/{rel_path}',
    )
    patch_content = "".join(diff)

    print(f"[DEBUG] '{change.action}' convertido a parche. Aplicando con git apply...")
    success, msg = apply_git_patch(project_path, patch_content)
    change.applied = success
    return success


def revert_change(change: Change, original_content: str) -> bool:
    if not os.path.exists(change.file_path):
        return False
    try:
        with open(change.file_path, 'w', encoding='utf-8') as f:
            f.write(original_content)
        change.applied = False
        return True
    except Exception:
        return False


def get_file_diff(change: Change) -> tuple:
    old_lines = change.old_code.strip().split('\n') if change.old_code else []
    new_lines = change.new_code.strip().split('\n') if change.new_code else []
    return old_lines, new_lines


def save_change(project_path: str, rel_path: str, old_code: str, new_code: str):
    """Guarda un cambio en el archivo _changes.txt"""
    changes_file = os.path.join(project_path, "_changes", "_changes.txt")
    
    change_block = f"""
<CAMBIOS>
  <ARCHIVO>{rel_path}</ARCHIVO>
  <ACCION>reemplazar</ACCION>
  <CODIGO_ANTIGUO>
{old_code}
  </CODIGO_ANTIGUO>
  <CODIGO_NUEVO>
{new_code}
  </CODIGO_NUEVO>
</CAMBIOS>
"""
    
    try:
        with open(changes_file, 'a', encoding='utf-8') as f:
            f.write(change_block)
    except Exception as e:
        print(f"Error al guardar cambio: {e}")
