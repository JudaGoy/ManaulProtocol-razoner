import os
from services.git_service import (
    get_status, get_history, commit, revert_file, discard_all_changes,
    get_default_commit_message,
    get_file_at_commit, get_current_file_content,
    get_uncommitted_files
)
from services.history_service import (
    clear_apply_history, clear_all_apply_history,
    get_files_with_history, get_history_snapshots
)


def get_git_status(project_path: str) -> dict:
    return get_status(project_path)


def get_last_commit_info(project_path: str) -> dict | None:
    history = get_history(project_path, limit=1)
    return history[0] if history else None


def get_files_with_changes(project_path: str) -> list:
    files_with_history = get_files_with_history(project_path)
    uncommitted_files = get_uncommitted_files(project_path)
    
    all_files = list(set(files_with_history + uncommitted_files))
    
    # Filtrar archivos ignorados explícitamente (.gitignore y _changes.txt)
    all_files = [f for f in all_files if f != '.gitignore' and not f.endswith('_changes.txt')]
    
    all_files.sort()
    
    return all_files


def get_file_status(project_path: str, filename: str) -> dict:
    snapshots = get_history_snapshots(project_path, filename)
    version_count = len(snapshots)
    
    uncommitted = get_uncommitted_files(project_path)
    is_uncommitted = filename in uncommitted
    
    history = get_history(project_path, limit=1)
    if history:
        last_commit_code = get_file_at_commit(project_path, "HEAD", filename)
        current_code = get_current_file_content(project_path, filename)
        has_diff_from_commit = last_commit_code != current_code
    else:
        has_diff_from_commit = True
    
    if version_count > 0:
        status_color = "orange"
    elif is_uncommitted:
        status_color = "red"
    else:
        status_color = "green"
    
    return {
        "version_count": version_count,
        "is_uncommitted": is_uncommitted,
        "has_diff_from_commit": has_diff_from_commit,
        "status_color": status_color
    }


def do_commit(project_path: str, message: str) -> tuple[bool, str]:
    success, result = commit(project_path, message)
    
    if success:
        clear_all_apply_history(project_path)
    
    return success, result


def do_revert_file(project_path: str, filename: str, commit_hash: str, watcher_holder: dict) -> tuple[bool, str]:
    success, result = revert_file(project_path, filename, commit_hash)
    
    if success:
        clear_apply_history(project_path, filename)
    
    return success, result


def do_discard_all_changes(project_path: str, watcher_holder: dict) -> tuple[bool, str]:
    success, msg = discard_all_changes(project_path)
    
    if success:
        git_status = get_status(project_path)
        untracked = git_status.get("untracked", [])
        
        for filepath in untracked:
            full_path = os.path.join(project_path, filepath)
            if os.path.isfile(full_path):
                try:
                    os.remove(full_path)
                except Exception:
                    pass
        
        clear_all_apply_history(project_path)
    
    return success, msg


def get_file_diff_data(project_path: str, filename: str, version_index: int = 0) -> dict:
    snapshots = get_history_snapshots(project_path, filename)
    version_count = len(snapshots)
    
    last_commit_code = get_file_at_commit(project_path, "HEAD", filename)
    current_code = get_current_file_content(project_path, filename)
    
    if not last_commit_code:
        last_commit_code = "(Archivo no existe en el último commit)"
    
    applied_code = current_code
    if version_count > 0 and version_index > 0:
        idx = version_index - 1
        if idx < len(snapshots):
            applied_code = snapshots[idx]
    
    diff_label = f"{filename}"
    if version_count > 0:
        diff_label += f" (Aplicado sin commit - {version_count})"
    elif last_commit_code and last_commit_code != current_code:
        diff_label += " (Modificado sin commit)"
    elif not last_commit_code:
        diff_label += " (Nuevo archivo)"
    else:
        diff_label += " (Sincronizado)"
    
    return {
        "original": last_commit_code,
        "modified": applied_code,
        "label": diff_label,
        "version_count": version_count
    }


def has_changes_to_commit(project_path: str) -> bool:
    status = get_status(project_path)
    
    all_changes = status["staged"] + status["modified"] + status["untracked"]
    # Verificar si hay cambios válidos ignorando los archivos de sistema
    valid_changes = [f for f in all_changes if f != '.gitignore' and not f.endswith('_changes.txt')]
    
    return bool(valid_changes)
