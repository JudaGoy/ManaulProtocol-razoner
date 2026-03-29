import os
from services.git_service import (
    get_status, get_history, commit, revert_file, discard_all_changes,
    get_default_commit_message,
    get_file_at_commit, get_current_file_content,
    get_uncommitted_files
)


def _filter_system_files(files: list) -> list:
    """Filtra archivos del sistema (_changes, .gitignore, etc)"""
    filtered = []
    for f in files:
        if f == '.gitignore':
            continue
        if '_changes' in f:
            continue
        filtered.append(f)
    return filtered


def get_git_status(project_path: str) -> dict:
    return get_status(project_path)


def get_last_commit_info(project_path: str) -> dict | None:
    history = get_history(project_path, limit=1)
    return history[0] if history else None


def get_files_with_changes(project_path: str) -> list:
    uncommitted_files = get_uncommitted_files(project_path)
    uncommitted_files = _filter_system_files(uncommitted_files)
    uncommitted_files.sort()
    return uncommitted_files


def get_file_status(project_path: str, filename: str) -> dict:
    uncommitted = get_uncommitted_files(project_path)
    is_uncommitted = filename in uncommitted
    
    history = get_history(project_path, limit=1)
    if history:
        last_commit_code = get_file_at_commit(project_path, "HEAD", filename)
        current_code = get_current_file_content(project_path, filename)
        has_diff_from_commit = last_commit_code != current_code
    else:
        has_diff_from_commit = True
    
    if is_uncommitted:
        status_color = "red"
    else:
        status_color = "green"
    
    return {
        "is_uncommitted": is_uncommitted,
        "has_diff_from_commit": has_diff_from_commit,
        "status_color": status_color
    }


def do_commit(project_path: str, message: str) -> tuple[bool, str]:
    success, result = commit(project_path, message)
    return success, result


def do_revert_file(project_path: str, filename: str, commit_hash: str, watcher_holder: dict) -> tuple[bool, str]:
    success, result = revert_file(project_path, filename, commit_hash)
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
    
    return success, msg


def get_file_diff_data(project_path: str, filename: str, version_index: int = 0) -> dict:
    last_commit_code = get_file_at_commit(project_path, "HEAD", filename)
    current_code = get_current_file_content(project_path, filename)
    
    if not last_commit_code:
        last_commit_code = "(Archivo no existe en el último commit)"
    
    diff_label = f"{filename}"
    if last_commit_code and last_commit_code != current_code:
        diff_label += " (Modificado sin commit)"
    elif not last_commit_code:
        diff_label += " (Nuevo archivo)"
    else:
        diff_label += " (Sincronizado)"
    
    return {
        "original": last_commit_code,
        "modified": current_code,
        "label": diff_label
    }


def has_changes_to_commit(project_path: str) -> bool:
    status = get_status(project_path)
    
    all_changes = status["staged"] + status["modified"] + status["untracked"]
    valid_changes = _filter_system_files(all_changes)
    
    return bool(valid_changes)
