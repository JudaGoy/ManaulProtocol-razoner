import os
import re
import html
import xml.etree.ElementTree as ET
from dataclasses import dataclass


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
    raw_xml: str = ""
    applied: bool = False


@dataclass  
class ChangeError:
    error_type: str
    message: str
    file_path: str
    detail: str


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
    
    print(f"\n[DEBUG] Contenido length (antes): {len(content)} chars")
    print(f"[DEBUG] Tiene system-reminder: {'<system-reminder>' in content}")
    
    content = re.sub(r'<system-reminder>.*?</system-reminder>', '', content, flags=re.DOTALL | re.IGNORECASE)
    content = re.sub(r'<system-.*?>.*?</system-.*?>', '', content, flags=re.DOTALL)
    
    print(f"[DEBUG] Contenido length (despues): {len(content)} chars")
    print(f"[DEBUG] Todavia tiene system-reminder: {'<system-reminder>' in content}")
    
    block_pattern = re.compile(r'<CAMBIOS>(.*?)</CAMBIOS>', re.DOTALL)
    blocks = block_pattern.findall(content)
    
    print(f"[DEBUG] Bloques <CAMBIOS> encontrados: {len(blocks)}")
    
    for i, block in enumerate(blocks):
        print(f"[DEBUG] === BLOQUE #{i+1} ===")
        
        archivo_match = re.search(r'<ARCHIVO>\s*(.+?)\s*</ARCHIVO>', block, re.DOTALL)
        if not archivo_match:
            continue
        
        accion_match = re.search(r'<ACCION>\s*(.+?)\s*</ACCION>', block, re.DOTALL)
        old_match = re.search(r'<CODIGO_ANTIGUO>\s*(.*?)\s*</CODIGO_ANTIGUO>', block, re.DOTALL)
        new_match = re.search(r'<CODIGO_NUEVO>\s*(.*?)\s*</CODIGO_NUEVO>', block, re.DOTALL)
        
        if not old_match or not new_match:
            print(f"[DEBUG] ERROR: No se encontro CODIGO_ANTIGUO o CODIGO_NUEVO")
            continue
        
        old_code = old_match.group(1)
        new_code = new_match.group(1)
        archivo = archivo_match.group(1).strip()
        accion = accion_match.group(1).strip().lower() if accion_match else ''
        
        print(f"[DEBUG] old_code RAW (primeros 200 chars):")
        print(repr(old_code[:200]))
        print(f"[DEBUG] old_code RAW length: {len(old_code)}")
        print(f"[DEBUG] old_code.strip() (primeros 200 chars):")
        print(repr(old_code.strip()[:200]))
        
        if archivo:
            abs_path = os.path.join(project_path, archivo)
            normalized_old = normalize_text(old_code.strip())
            normalized_new = normalize_text(new_code.strip())
            
            print(f"[DEBUG] archivo: {archivo}")
            print(f"[DEBUG] accion: {accion}")
            print(f"[DEBUG] old_code length: {len(normalized_old)}")
            print(f"[DEBUG] new_code length: {len(normalized_new)}")
            
            changes.append(Change(
                file_path=abs_path,
                action=accion,
                old_code=normalized_old,
                new_code=normalized_new,
                raw_xml=f"<CAMBIOS>{block}</CAMBIOS>"
            ))
    
    return changes, errors


def get_original_code(change: Change) -> str:
    if not os.path.exists(change.file_path):
        return ""
    try:
        with open(change.file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception:
        return ""


def apply_change(change: Change) -> bool:
    print(f"\n[DEBUG apply_change] ===")
    print(f"[DEBUG] archivo: {change.file_path}")
    print(f"[DEBUG] action: {change.action}")
    
    try:
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
        
        if change.action == 'insertar':
            if not os.path.exists(change.file_path):
                return False
            with open(change.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            old_code_stripped = change.old_code.strip()
            if old_code_stripped and old_code_stripped in content:
                new_content = content.replace(old_code_stripped, old_code_stripped + "\n" + change.new_code, 1)
                with open(change.file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                change.applied = True
                return True
            return False
        
        if not os.path.exists(change.file_path):
            return False
        
        with open(change.file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        old_code_stripped = change.old_code.strip()
        
        if not old_code_stripped:
            print(f"[DEBUG ERROR] old_code está vacío después de strip()")
            return False
        
        print(f"[DEBUG] old_code length: {len(old_code_stripped)}")
        print(f"[DEBUG] content length: {len(content)}")
        print(f"[DEBUG] old_code (primeros 200 chars):")
        print(repr(old_code_stripped[:200]))
        print(f"[DEBUG] old_code count newlines: {old_code_stripped.count(chr(10))}")
        
        if old_code_stripped in content:
            new_content = content.replace(old_code_stripped, change.new_code, 1)
            with open(change.file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            change.applied = True
            print(f"[DEBUG] ✓ Cambio aplicado exitosamente")
            return True
        
        # ===== DEBUG: Diagnóstico de por qué NO coincidió =====
        print(f"[DEBUG] === ERROR: Código no encontrado en archivo ===")
        
        # Buscar primera línea del código
        first_line = old_code_stripped.split('\n')[0][:50] if '\n' in old_code_stripped else old_code_stripped[:50]
        print(f"[DEBUG] Primera línea buscada: {repr(first_line)}")
        print(f"[DEBUG] Primera línea ENCONTRADA en archivo: {first_line in content}")
        
        # Buscar variaciones comunes
        first_line_stripped = first_line.strip()
        print(f"[DEBUG] Primera línea sin espacios: {repr(first_line_stripped)}")
        print(f"[DEBUG] Primera línea sin espacios ENCONTRADA: {first_line_stripped in content}")
        
        # Mostrar contexto del archivo donde debería estar
        if first_line_stripped and first_line_stripped in content:
            idx = content.find(first_line_stripped)
            print(f"[DEBUG] Contexto en archivo (50 chars antes y después):")
            print(repr(content[max(0,idx-50):idx+150]))
            print(f"[DEBUG] Línea con indentación real:")
            lines_before = content[:idx].count('\n')
            line_start = content.rfind('\n', 0, idx) + 1
            line_end = content.find('\n', idx)
            actual_line = content[line_start:line_end if line_end != -1 else len(content)]
            print(f"[DEBUG] Línea real #{lines_before + 1}: {repr(actual_line[:80])}")
        
        return False
        
    except Exception as e:
        print(f"[DEBUG ERROR] Excepción: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


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
    """Retorna (old_lines, new_lines) para mostrar en el UI."""
    old_lines = change.old_code.strip().split('\n') if change.old_code else []
    new_lines = change.new_code.strip().split('\n') if change.new_code else []
    return old_lines, new_lines
