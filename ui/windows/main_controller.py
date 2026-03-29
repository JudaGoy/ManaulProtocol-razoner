import os
from services.project_service import initialize_project


def initialize_project_service(project_path: str) -> tuple[bool, str, str]:
    return initialize_project(project_path)


def get_selected_files(selected_files: dict) -> list:
    return [path for path, selected in selected_files.items() if selected]


def validate_project_for_changes(project_path: str) -> tuple[bool, str]:
    if not project_path:
        return False, "Selecciona un proyecto primero"
    
    changes_file = os.path.join(project_path, "_changes", "_changes.txt")
    
    if not os.path.exists(os.path.dirname(changes_file)):
        return False, "La carpeta _changes no existe"
    
    return True, ""


def ensure_changes_file(project_path: str) -> str:
    changes_folder = os.path.join(project_path, "_changes")
    if not os.path.exists(changes_folder):
        os.makedirs(changes_folder, exist_ok=True)
    
    changes_file = os.path.join(changes_folder, "_changes.txt")
    if not os.path.exists(changes_file):
        with open(changes_file, 'w', encoding='utf-8') as f:
            f.write("")
    
    return changes_file
