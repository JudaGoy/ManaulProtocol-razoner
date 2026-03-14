import os
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Change:
    file_path: str
    action: str
    position_type: str
    start_line: Optional[int]
    end_line: Optional[int]
    code: str
    original_lines: Optional[List[str]] = None
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
    
    content = content.strip()
    
    cambio_blocks = content.split('</CAMBIOS>')
    
    for block in cambio_blocks:
        if '<CAMBIOS>' not in block:
            continue
        
        block = block + '</CAMBIOS>'
        
        try:
            block_clean = block.strip()
            if not block_clean.startswith('<'):
                continue
                
            root = ET.fromstring(block_clean)
            
            archivo = root.findtext('ARCHIVO', '').strip()
            accion = root.findtext('ACCION', '').strip().lower()
            
            posicion = root.find('POSICION')
            if posicion is not None:
                tipo = posicion.findtext('TIPO', 'lineas').strip().lower()
                inicio = posicion.findtext('INICIO', '').strip()
                fin = posicion.findtext('FIN', '').strip()
            else:
                tipo = 'lineas'
                inicio = ''
                fin = ''
            
            codigo_elem = root.find('CODIGO')
            if codigo_elem is not None:
                codigo = codigo_elem.text or ''
            else:
                codigo = ''
            
            codigo = codigo.strip()
            
            if archivo:
                abs_path = os.path.join(project_path, archivo)
                
                change = Change(
                    file_path=abs_path,
                    action=accion,
                    position_type=tipo,
                    start_line=int(inicio) if inicio else None,
                    end_line=int(fin) if fin else None,
                    code=codigo
                )
                
                changes.append(change)
                
        except ET.ParseError as e:
            errors.append(ChangeError(
                error_type="xml_invalido",
                message="Error al parsear XML",
                file_path="",
                detail=str(e)
            ))
        except Exception as e:
            errors.append(ChangeError(
                error_type="desconocido",
                message="Error desconocido",
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


def get_original_lines(change: Change) -> List[str]:
    if not os.path.exists(change.file_path):
        return []
    
    try:
        with open(change.file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        if change.position_type == 'inicio':
            return lines[:1] if lines else []
        elif change.position_type == 'final':
            return lines[-1:] if lines else []
        elif change.start_line and change.end_line:
            start_idx = max(0, change.start_line - 1)
            end_idx = min(len(lines), change.end_line)
            return lines[start_idx:end_idx]
        elif change.start_line:
            idx = max(0, change.start_line - 1)
            return [lines[idx]] if idx < len(lines) else []
        
        return []
        
    except Exception:
        return []


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
                f.write(change.code)
            change.applied = True
            return True
        
        if not os.path.exists(change.file_path):
            return False
        
        with open(change.file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        new_code_lines = change.code.split('\n')
        
        if change.position_type == 'inicio':
            lines = new_code_lines + ['\n'] + lines
        elif change.position_type == 'final':
            if lines and lines[-1] != '\n':
                lines[-1] = lines[-1] + '\n'
            lines.extend(['\n'] + new_code_lines)
        elif change.action == 'eliminar':
            if change.start_line and change.end_line:
                start_idx = max(0, change.start_line - 1)
                end_idx = min(len(lines), change.end_line)
                lines = lines[:start_idx] + lines[end_idx:]
        elif change.start_line and change.end_line:
            start_idx = max(0, change.start_line - 1)
            end_idx = min(len(lines), change.end_line)
            lines = lines[:start_idx] + new_code_lines + ['\n'] + lines[end_idx:]
        elif change.start_line:
            idx = max(0, change.start_line - 1)
            lines = lines[:idx] + new_code_lines + ['\n'] + lines[idx + 1:]
        
        with open(change.file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        change.applied = True
        return True
        
    except Exception as e:
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
            return [], [f"📄 Crear archivo con contenido:", change.code]
        
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
        
        if not os.path.exists(change.file_path):
            return [], []
        
        with open(change.file_path, 'r', encoding='utf-8') as f:
            current_lines = f.readlines()
        
        new_code_lines = change.code.split('\n')
        
        old_lines = []
        
        if change.position_type == 'inicio':
            old_lines = current_lines[:len(new_code_lines)] if current_lines else []
        elif change.position_type == 'final':
            old_lines = current_lines[-len(new_code_lines):] if current_lines else []
        elif change.start_line and change.end_line:
            start_idx = max(0, change.start_line - 1)
            end_idx = min(len(current_lines), change.end_line)
            old_lines = current_lines[start_idx:end_idx]
        
        return old_lines, new_code_lines
        
    except Exception:
        return [], []
