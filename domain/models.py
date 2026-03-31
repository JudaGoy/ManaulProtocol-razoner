import os
import re
import html
import difflib
from dataclasses import dataclass
from typing import List, Tuple

from domain.security import is_safe_path

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False

try:
    import ftfy
    FTFY_AVAILABLE = True
except ImportError:
    FTFY_AVAILABLE = False


def _strip_markdown_wrapper(content: str) -> str:
    """Extrae XML de bloques ```xml ... ``` o ``` ... ```"""
    match = re.search(r'```(?:xml)?\s*(.*?)\s*```', content, re.DOTALL)
    if match:
        return match.group(1).strip()
    return content


def _normalize_xml_content(content: str) -> str:
    """Normaliza contenido XML: normaliza espacios a un solo espacio."""
    if not content:
        return content
    content = re.sub(r'<(\w+)([^>]*)\s*/>', r'<\1\2></\1>', content)
    content = re.sub(r'\s+', ' ', content)
    content = content.strip()
    return content


def _extract_raw_xml_content(block_xml: str, tag_name: str) -> str:
    """Extrae contenido raw de etiquetas XML usando regex para preservar formato."""
    pattern = rf'<{tag_name}>(.*?)</{tag_name}>'
    match = re.search(pattern, block_xml, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return ""


def _get_parser_features():
    """Retorna el parser para BeautifulSoup, con fallback a html.parser"""
    if not BS4_AVAILABLE:
        return None
    try:
        soup = BeautifulSoup("<test></test>", features='xml')
        return 'xml'
    except Exception:
        return 'html'


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


def normalize_code_text(text: str) -> str:
    """Normaliza texto de código para comparación robusta."""
    if not text:
        return text
    
    if FTFY_AVAILABLE:
        text = ftfy.fix_text(text)
    
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    
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
    report_id: str = ""
    status: str = "PENDING"
    error_detail: str = ""


@dataclass
class ChangeError(Exception):
    error_type: str
    message: str
    file_path: str
    detail: str = ""
    
    def __str__(self):
        return f"[{self.error_type}] {self.message} | Archivo: {self.file_path}"
    
    def to_report(self, raw_xml: str = "") -> str:
        detail = self.detail if self.detail else "N/A"
        report = f"""ERROR DE APLICACIÓN: {self.message}
- Tipo de error: {self.error_type}
- Archivo: {self.file_path}
- Detalle: {detail}"""
        if raw_xml:
            report += f"""
- Bloque XML original:
{raw_xml}"""
        return report


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
    
    content = _strip_markdown_wrapper(content)
    
    if BS4_AVAILABLE:
        try:
            features = _get_parser_features()
            soup = BeautifulSoup(content, features=features)
            
            all_blocks = soup.find_all(['cambios', 'CAMBIOS', 'block', 'BLOCK'])
            
            block_matches = re.findall(r'(<CAMBIOS>.*?</CAMBIOS>)', content, re.DOTALL | re.IGNORECASE)
            
            for idx, block_match_str in enumerate(block_matches):
                block_xml = block_match_str
                block_soup = BeautifulSoup(block_xml, features=features)
                block = block_soup.find(['cambios', 'CAMBIOS', 'block', 'BLOCK'])
                
                if not block:
                    continue
                
                archivos = block.find_all(['archivo', 'ARCHIVO', 'file', 'FILE'])
                if not archivos:
                    archivos = [block] if block.find(['archivo', 'ARCHIVO']) else []
                
                for archivo_tag in archivos:
                    archivo_elem = archivo_tag.find(['archivo', 'ARCHIVO', 'file', 'FILE'])
                    if archivo_elem:
                        archivo = archivo_elem.get_text()
                    else:
                        archivo = archivo_tag.get_text()
                    
                    archivo = archivo.strip()
                    if not archivo:
                        continue
                    
                    accion_elem = block.find(['accion', 'ACCION', 'action', 'ACTION'])
                    accion = accion_elem.get_text().strip().lower() if accion_elem else ''
                    
                    old_code = _extract_raw_xml_content(block_xml, 'codigo_antiguo')
                    if not old_code:
                        old_code = _extract_raw_xml_content(block_xml, 'CODIGO_ANTIGUO')
                    if not old_code:
                        old_code = _extract_raw_xml_content(block_xml, 'old_code')
                    
                    new_code = _extract_raw_xml_content(block_xml, 'codigo_nuevo')
                    if not new_code:
                        new_code = _extract_raw_xml_content(block_xml, 'CODIGO_NUEVO')
                    if not new_code:
                        new_code = _extract_raw_xml_content(block_xml, 'new_code')
                    
                    if accion in ['crear', 'crear_carpeta', 'eliminar_archivo', 'eliminar_carpeta', 'eliminar', 'reemplazar']:
                        if not new_code and accion in ['crear', 'crear_carpeta']:
                            continue
                    else:
                        if not old_code or not new_code:
                            continue
                    
                    instancias_elem = block.find(['instancias', 'INSTANCIAS', 'instances', 'INSTANCES'])
                    instances = instancias_elem.get_text().strip() if instancias_elem else "all"
                    
                    id_reporte_elem = block.find(['id_reporte', 'ID_REPORTE', 'report_id', 'REPORT_ID'])
                    report_id = id_reporte_elem.get_text().strip() if id_reporte_elem else ""
                    
                    if not report_id:
                        errors.append(ChangeError(
                            error_type="validacion_id",
                            message="[STRICT_ERROR] ID_REPORTE faltante en bloque",
                            file_path=archivo,
                            detail="Todo bloque debe tener <ID_REPORTE>nombre_HHMMSS</ID_REPORTE>"
                        ))
                        continue
                    
                    if not accion and ('diff --git' in new_code or ('--- a/' in new_code and '+++ b/' in new_code)):
                        accion = 'patch'
                    
                    abs_path = os.path.join(project_path, archivo)
                    old_code_raw = old_code
                    new_code_raw = new_code
                    
                    changes.append(Change(
                        file_path=abs_path,
                        action=accion,
                        old_code=old_code_raw,
                        new_code=new_code_raw,
                        instances=instances,
                        raw_xml=block_xml,
                        report_id=report_id,
                        status="PENDING"
                    ))
        except Exception as e:
            errors.append(ChangeError(
                error_type="parser_error",
                message=f"Error al parsear XML con BeautifulSoup: {e}",
                file_path="",
                detail=str(e)
            ))
    else:
        block_pattern = re.compile(r'(<CAMBIOS>.*?</CAMBIOS>)', re.DOTALL)
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
            
            id_reporte_match = re.search(r'<ID_REPORTE>\s*(.+?)\s*</ID_REPORTE>', block, re.DOTALL)
            report_id = id_reporte_match.group(1).strip() if id_reporte_match else ""
            
            if not report_id:
                errors.append(ChangeError(
                    error_type="validacion_id",
                    message="[STRICT_ERROR] ID_REPORTE faltante en bloque",
                    file_path=archivo,
                    detail="Todo bloque debe tener <ID_REPORTE>nombre_HHMMSS</ID_REPORTE>"
                ))
                continue
            
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
                    raw_xml=block,
                    report_id=report_id,
                    status="PENDING"
                ))
    
    return changes, errors


def apply_change(change: Change, project_path: str = None) -> bool:
    try:
        if project_path and not is_safe_path(project_path, change.file_path):
            raise ChangeError(
                error_type="ruta_insegura",
                message=f"Ruta fuera del proyecto: {change.file_path}",
                file_path=change.file_path,
                detail=f"Proyecto: {project_path}"
            )

        from services.git_service import apply_git_patch
        
        if change.action == 'patch' or change.action == 'parche':
            if not project_path:
                raise ChangeError(
                    error_type="project_path_requerido",
                    message="Se requiere project_path para aplicar parches",
                    file_path=change.file_path
                )
            
            success, msg = apply_git_patch(project_path, change.new_code)
            if not success:
                raise ChangeError(
                    error_type="git_apply_fallo",
                    message=f"Git apply falló: {msg}",
                    file_path=change.file_path,
                    detail=change.new_code[:500]
                )
            change.applied = success
            return success

        if change.action in ['reemplazar', 'insertar', 'eliminar']:
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
        
    except ChangeError:
        raise
    except Exception as e:
        raise ChangeError(
            error_type="excepcion_desconocida",
            message=f"{type(e).__name__}: {e}",
            file_path=change.file_path,
            detail=str(e)
        ) from e


def _apply_text_change_as_patch(change: Change, project_path: str) -> bool:
    from services.git_service import apply_git_patch
    
    if not is_safe_path(project_path, change.file_path):
        raise ChangeError(
            error_type="ruta_insegura",
            message=f"Ruta fuera del proyecto: {change.file_path}",
            file_path=change.file_path,
            detail=f"Proyecto: {project_path}"
        )
    
    if not project_path:
        raise ChangeError(
            error_type="project_path_requerido",
            message=f"Se requiere project_path para aplicar '{change.action}'",
            file_path=change.file_path
        )
    if not os.path.exists(change.file_path):
        raise ChangeError(
            error_type="archivo_no_encontrado",
            message=f"Archivo no encontrado: {change.file_path}",
            file_path=change.file_path,
            detail=f"Acción: {change.action}"
        )

    print(f"[DEBUG apply_change] Procesando {change.action.upper()} para {os.path.basename(change.file_path)}")
    
    with open(change.file_path, 'r', encoding='utf-8') as f:
        original_content = f.read()
    
    target_old_code = change.old_code
    target_new_code = change.new_code
    
    if not target_old_code.strip():
        raise ChangeError(
            error_type="old_code_vacio",
            message="El código a buscar ('old_code') está vacío o solo contiene espacios",
            file_path=change.file_path
        )

    use_normalized = False
    original_content_raw = ""
    
    with open(change.file_path, 'r', encoding='utf-8') as f:
        original_content_raw = f.read()
    
    original_content = original_content_raw
    
    if target_old_code in original_content:
        print("[DEBUG] -> Coincidencia exacta encontrada (sin normalización).")
    else:
        print("[DEBUG] ! Primer intento sin normalización falló.")
        print("[DEBUG] -> Reintentando con código normalizado...")
        
        normalized_original = normalize_code_text(original_content)
        normalized_old = re.sub(r'\s+', ' ', target_old_code)
        normalized_new = re.sub(r'\s+', ' ', target_new_code)
        
        if normalized_old not in normalized_original:
            normalized_original = re.sub(r'\s+', ' ', original_content)
            if normalized_old not in normalized_original:
                raise ChangeError(
                    error_type="error_coincidencia",
                    message="ERROR_MATCH: Coincidencia exacta no encontrada (ni con normalización).",
                    file_path=change.file_path,
                    detail="El código antiguo proporcionado no coincide con el archivo, ni siquiera después de normalizar caracteres."
                )
        
        print("[DEBUG] -> Coincidencia encontrada con normalización.")
        use_normalized = True
        original_content = normalized_original
        target_old_code = normalized_old
        target_new_code = normalized_new

    if change.action == 'reemplazar':
        new_content = replace_specific_instances(original_content, target_old_code, target_new_code, change.instances)
    elif change.action == 'insertar':
        # Validar que CODIGO_ANTIGUO no esté contenido en CODIGO_NUEVO (duplicado)
        if target_old_code in target_new_code:
            raise ChangeError(
                error_type="insertar_duplicado",
                message="CODIGO_ANTIGUO está contenido en CODIGO_NUEVO. "
                        "La IA posiblemente copió el código antiguo en el nuevo, causando duplicado. "
                        "En acción 'insertar', CODIGO_NUEVO debe contener SOLO el código nuevo a añadir.",
                file_path=change.file_path,
                detail=f"El código antiguo aparece {target_new_code.count(target_old_code)} vez(es) en el código nuevo"
            )
        new_content = original_content.replace(target_old_code, target_old_code + "\n" + target_new_code, 1)
    elif change.action == 'eliminar':
        new_content = replace_specific_instances(original_content, target_old_code, "", change.instances)
    else:
        print(f"[DEBUG] Acción no reconocida: {change.action}")
        return False

    if original_content == new_content:
        print("[DEBUG] ! AVISO: La operación no resulted en cambios. Se considera exitoso.")
        change.applied = True
        return True

    if use_normalized:
        new_content_for_diff = replace_specific_instances(
            re.sub(r'\s+', ' ', original_content_raw), 
            target_old_code, 
            target_new_code, 
            change.instances
        )
    else:
        new_content_for_diff = new_content

    rel_path = os.path.relpath(change.file_path, project_path).replace('\\', '/')
    
    if new_content_for_diff != (re.sub(r'\s+', ' ', original_content_raw) if use_normalized else original_content):
        diff = difflib.unified_diff(
            original_content.splitlines(keepends=True),
            new_content.splitlines(keepends=True),
            fromfile=f'a/{rel_path}',
            tofile=f'b/{rel_path}',
        )
        patch_content = "".join(diff)
        
        if not patch_content.strip():
            print("[DEBUG] Parche vacío, escribiendo cambio directamente...")
            if use_normalized:
                final_content = original_content_raw.replace(change.old_code.strip(), change.new_code.strip())
            else:
                final_content = new_content
            with open(change.file_path, 'w', encoding='utf-8') as f:
                f.write(final_content)
            change.applied = True
            return True

        print(f"[DEBUG] '{change.action}' convertido a parche. Aplicando con git apply...")
        success, msg = apply_git_patch(project_path, patch_content)
    else:
        print("[DEBUG] Sin cambios efectivos, aplicando escritura directa...")
        if use_normalized:
            final_content = original_content_raw.replace(change.old_code.strip(), change.new_code.strip())
        else:
            final_content = new_content
        with open(change.file_path, 'w', encoding='utf-8') as f:
            f.write(final_content)
        change.applied = True
        success = True
        msg = "Escritura directa"
    
    if not success:
        print(f"[DEBUG] Git apply falló: {msg}, escribiendo directamente...")
        if use_normalized:
            final_content = original_content_raw.replace(change.old_code.strip(), change.new_code.strip())
        else:
            final_content = new_content
        with open(change.file_path, 'w', encoding='utf-8') as f:
            f.write(final_content)
        change.applied = True
        return True
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
