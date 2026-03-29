import os
import re
from domain.models import Change, apply_change, get_file_diff, parse_xml_content, normalize_text, ChangeError
from services.project_service import (
    generate_error_report, setup_logging, log_session_start, log_session_end,
    log_change_success, log_change_error
)
from services.report_service import register_report, clear_reports, generate_ia_report
from services.git_service import (
    get_status, get_history, commit, get_file_at_commit, 
    get_current_file_content, revert_file, get_modified_files_since_commit,
    get_commit_files, get_uncommitted_files, discard_all_changes,
    get_default_commit_message
)


def load_changes(project_path: str, changes_file: str) -> tuple[list, list]:
    clear_reports()
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
    try:
        success = apply_change(change, project_path)
        if success:
            if change.report_id:
                register_report(change.report_id, "OK")
            return True, ""
        else:
            if change.report_id:
                register_report(change.report_id, "ERROR", "Aplicación fallida")
            return False, "La IA puede haber generado código incorrecto o el archivo cambió."
    except ChangeError as e:
        if change.report_id:
            register_report(change.report_id, "ERROR", str(e))
        return False, str(e)


def accept_all_changes(project_path: str, changes: list, watcher_holder: dict) -> tuple[int, list, list]:
    setup_logging(project_path)
    log_session_start(project_path)
    
    accepted_count = 0
    indices_to_accept = []
    failed_errors = []
    
    for i, change in enumerate(changes):
        try:
            success = apply_change(change, project_path)
            
            if success:
                log_change_success(change.file_path, change.action)
                if change.report_id:
                    register_report(change.report_id, "OK")
                accepted_count += 1
                indices_to_accept.append(i)
            else:
                raise ChangeError(
                    error_type="aplicacion_fallida",
                    message="El cambio no pudo ser aplicado",
                    file_path=change.file_path
                )
        except ChangeError as e:
            log_change_error(change.file_path, change.action, e)
            if change.report_id:
                register_report(change.report_id, "ERROR", str(e))
            failed_errors.append((change, e))
            continue
    
    log_session_end(accepted_count, len(failed_errors))
    
    return accepted_count, indices_to_accept, failed_errors


def remove_applied_block(changes_file: str, change: Change):
    content = ""
    try:
        with open(changes_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception:
        return
    
    # Normalizar contenido a \n para evitar problemas de Windows/Linux (CRLF)
    content_norm = content.replace('\r\n', '\n')
    new_content_norm = content_norm
    
    if hasattr(change, 'raw_xml') and change.raw_xml:
        # Normalizar también el bloque que buscamos
        raw_norm = change.raw_xml.replace('\r\n', '\n')
        
        if raw_norm in content_norm:
            new_content_norm = content_norm.replace(raw_norm, "", 1)
        else:
            # Intento robusto con Regex ignorando espacios/saltos exactos
            try:
                raw_stripped = raw_norm.strip()
                pattern = re.escape(raw_stripped).replace(r'\n', r'\s*')
                new_content_norm = re.sub(pattern, "", content_norm, count=1, flags=re.DOTALL)
            except Exception:
                pass
    
    if new_content_norm != content_norm:
        # Limpiar saltos de línea múltiples residuales
        new_content_norm = re.sub(r'\n{3,}', '\n\n', new_content_norm)
        with open(changes_file, 'w', encoding='utf-8') as f:
            f.write(new_content_norm)


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


def get_failed_tasks_report(failed_errors: list) -> str:
    if not failed_errors:
        return ""
    
    report = "# TAREAS FALLIDAS\n\n"
    report += f"Se fallaron {len(failed_errors)} tarea(s). Por favor, genera nuevos cambios.\n\n"
    
    for i, (change, error) in enumerate(failed_errors, 1):
        report += f"## Tarea Fallida #{i}\n"
        report += generate_error_report(error, change.raw_xml)
        report += "\n\n"
    
    return report


def print_failed_tasks_report(failed_errors: list):
    report = get_failed_tasks_report(failed_errors)
    if report:
        print("\n" + "=" * 60)
        print(report)
        print("=" * 60)
