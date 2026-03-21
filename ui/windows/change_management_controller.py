import os
import re
from domain.models import Change, apply_change, get_file_diff, parse_xml_content, normalize_text
from services.history_service import apply_change_with_history, get_history_snapshots, clear_apply_history, clear_all_apply_history
from services.git_service import (
    get_status, get_history, commit, get_file_at_commit, 
    get_current_file_content, revert_file, get_modified_files_since_commit,
    get_commit_files, get_uncommitted_files, discard_all_changes,
    get_default_commit_message
)


def remove_applied_block(changes_file: str, change: Change):
    content = ""
    try:
        with open(changes_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception:
        return
    
    if not hasattr(change, 'file_path') or not change.file_path:
        return
    
    rel_path = os.path.relpath(change.file_path, os.path.dirname(os.path.dirname(changes_file)))
    
    pattern = re.compile(
        r'<CAMBIOS>.*?<ARCHIVO>\s*' + re.escape(rel_path) + r'\s*</ARCHIVO>.*?</CAMBIOS>',
        re.DOTALL
    )
    
    new_content = pattern.sub('', content)
    
    if new_content != content:
        new_content = new_content.strip()
        while "\n\n\n" in new_content:
            new_content = new_content.replace("\n\n\n", "\n\n")
        new_content = new_content.strip() + "\n"
        
        with open(changes_file, 'w', encoding='utf-8') as f:
            f.write(new_content)


def load_changes(project_path: str, changes_file: str) -> tuple[list, list]:
    changes = []
    errors = []
    
    try:
        with open(changes_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if content.strip():
            changes, errors = parse_xml_content(content, project_path)
    except Exception:
        pass
    
    return changes, errors


def accept_change(project_path: str, change: Change, watcher_holder: dict) -> tuple[bool, str]:
    rel_path = os.path.relpath(change.file_path, project_path)
    
    if change.action in ['crear_carpeta', 'crear', 'eliminar_archivo', 'eliminar_carpeta']:
        original_code = get_file_at_commit(project_path, "HEAD", rel_path)
        if not original_code:
            original_code = ""
        
        success = apply_change(change, project_path)
        
        if success:
            save_change_to_file(project_path, rel_path, change)
            return True, ""
        else:
            return False, "La IA puede haber generado código incorrecto o el archivo cambió."
    
    else:
        original_code = get_file_at_commit(project_path, "HEAD", rel_path)
        if original_code is None:
            original_code = ""

        success, error_msg = apply_change_with_history(project_path, change, original_code)
        
        if success:
            return True, ""
        else:
            return False, error_msg


def save_change_to_file(project_path: str, rel_path: str, change: Change):
    changes_file = os.path.join(project_path, "_changes", "_changes.txt")
    
    old_code = ""
    if change.action == 'eliminar':
        old_code = get_file_at_commit(project_path, "HEAD", rel_path) or ""
    
    change_block = f"""
<CAMBIOS>
  <ARCHIVO>{rel_path}</ARCHIVO>
  <ACCION>reemplazar</ACCION>
  <CODIGO_ANTIGUO>
{old_code}
  </CODIGO_ANTIGUO>
  <CODIGO_NUEVO>
{change.new_code}
  </CODIGO_NUEVO>
</CAMBIOS>
"""
    
    try:
        with open(changes_file, 'a', encoding='utf-8') as f:
            f.write(change_block)
    except Exception as e:
        print(f"Error al guardar cambio: {e}")


def accept_all_changes(project_path: str, changes: list, watcher_holder: dict) -> tuple[int, list]:
    accepted_count = 0
    indices_to_accept = []
    
    for i, change in enumerate(changes):
        rel_path = os.path.relpath(change.file_path, project_path)
        
        if change.action in ['crear_carpeta', 'crear', 'eliminar_archivo', 'eliminar_carpeta']:
            original_code = get_file_at_commit(project_path, "HEAD", rel_path)
            if not original_code:
                original_code = ""
            
            success = apply_change(change, project_path)
            if success:
                save_change_to_file(project_path, rel_path, change)
                accepted_count += 1
                indices_to_accept.append(i)
        else:
            original_code = get_file_at_commit(project_path, "HEAD", rel_path)
            if original_code is None:
                original_code = ""

            success, error_msg = apply_change_with_history(project_path, change, original_code)

            if success:
                accepted_count += 1
                indices_to_accept.append(i)
    
    return accepted_count, indices_to_accept


def get_action_text(action: str) -> str:
    return {
        'reemplazar': '🔄 Reemplazar',
        'insertar': '➕ Insertar',
        'eliminar': '🗑️ Eliminar',
        'crear': '✨ Crear archivo',
        'crear_carpeta': '📁 Crear carpeta',
        'eliminar_archivo': '🗑️ Eliminar archivo',
        'eliminar_carpeta': '🗑️ Eliminar carpeta',
        'patch': '🔧 Parche Git',
        'parche': '🔧 Parche Git'
    }.get(action, action)
