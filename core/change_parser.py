import os
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import List, Optional


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
    
    import re
    
    # Buscar bloques usando una estrategia más robusta
    # Encontrar todas las posiciones de <CAMBIOS> y </CAMBIOS>
    start_positions = [m.start() for m in re.finditer(r'<CAMBIOS>', content)]
    end_positions = [m.end() for m in re.finditer(r'</CAMBIOS>', content)]
    
    # Emparejar starts con ends
    blocks = []
    for start in start_positions:
        # Encontrar el </CAMBIOS> más cercano después de este start
        for end in end_positions:
            if end > start:
                blocks.append(content[start:end])
                break
    
    for block in blocks:
        try:
            # Extraer ARCHIVO
            archivo_match = re.search(r'<ARCHIVO>([^<]+)</ARCHIVO>', block)
            if not archivo_match:
                continue
            
            # Extraer ACCION
            accion_match = re.search(r'<ACCION>([^<]+)</ACCION>', block)
            
            # Extraer CODIGO_ANTIGUO
            old_code = ""
            old_start = block.find('<CODIGO_ANTIGUO>')
            if old_start != -1:
                old_start += len('<CODIGO_ANTIGUO>')
                old_end = block.find('</CODIGO_ANTIGUO>', old_start)
                if old_end != -1:
                    old_code = block[old_start:old_end]
            
            # Extraer CODIGO_NUEVO
            new_code = ""
            new_start = block.find('<CODIGO_NUEVO>')
            if new_start != -1:
                new_start += len('<CODIGO_NUEVO>')
                new_end = block.find('</CODIGO_NUEVO>', new_start)
                if new_end != -1:
                    new_code = block[new_start:new_end]
            
            archivo = archivo_match.group(1).strip()
            accion = accion_match.group(1).strip().lower() if accion_match else ''
            
            if archivo:
                abs_path = os.path.join(project_path, archivo)
                
                change = Change(
                    file_path=abs_path,
                    action=accion,
                    old_code=old_code.strip(),
                    new_code=new_code.strip(),
                    raw_xml=block
                )
                
                changes.append(change)
                
        except Exception as e:
            errors.append(ChangeError(
                error_type="desconocido",
                message="Error al parsear bloque",
                file_path="",
                detail=str(e)
            ))
    
    error_blocks = content.split('</ERROR>')
    
    for block in error_blocks:
        if '<ERROR>' not in block:
            continue
        
        block = block + '</ERROR>'
        
        try:
            root = ET.fromstring(block.strip())
            
            error_type = root.findtext('TIPO', '').strip()
            message = root.findtext('MENSAJE', '').strip()
            file_path = root.findtext('ARCHIVO', '').strip()
            detail = root.findtext('DETALLE', '').strip()
            
            errors.append(ChangeError(
                error_type=error_type,
                message=message,
                file_path=file_path,
                detail=detail
            ))
            
        except ET.ParseError:
            pass
    
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
                if new_content != content:
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
        content_stripped = content.strip()
        
        if not old_code_stripped:
            return False
        
        if old_code_stripped in content_stripped:
            new_content = content.replace(change.old_code, change.new_code, 1)
            if new_content == content:
                new_content = content.replace(change.old_code.strip(), change.new_code, 1)
        else:
            return False
        
        with open(change.file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        change.applied = True
        return True
        
    except Exception as e:
        print(f"DEBUG exception: {e}")
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
    try:
        if change.action == 'crear_carpeta':
            return [], [f"📁 Crear carpeta: {os.path.basename(change.file_path)}"]
        
        if change.action == 'crear':
            return [], [f"📄 Crear archivo con contenido:", change.new_code]
        
        if change.action == 'eliminar_archivo':
            if os.path.exists(change.file_path):
                try:
                    with open(change.file_path, 'r', encoding='utf-8') as f:
                        return [f.read()], ["(archivo eliminado)"]
                except:
                    return ["(no se pudo leer)"], ["(archivo eliminado)"]
            return [], ["(archivo ya no existe)"]
        
        if change.action == 'eliminar_carpeta':
            return [], [f"🗑️ Eliminar carpeta: {os.path.basename(change.file_path)}"]
        
        old_lines = change.old_code.split('\n') if change.old_code else []
        new_lines = change.new_code.split('\n') if change.new_code else []
        
        return old_lines, new_lines
        
    except Exception:
        return [], []
