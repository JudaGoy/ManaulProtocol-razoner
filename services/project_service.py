import os
from services.git_service import init_git, is_git_repo


def create_changes_directory(project_path: str) -> str:
    changes_folder = os.path.join(project_path, "_changes")
    if not os.path.exists(changes_folder):
        os.makedirs(changes_folder, exist_ok=True)
    return changes_folder


def create_changes_file(project_path: str) -> str:
    changes_folder = create_changes_directory(project_path)
    changes_file = os.path.join(changes_folder, "_changes.txt")
    if not os.path.exists(changes_file):
        with open(changes_file, 'w', encoding='utf-8') as f:
            f.write("")
    return changes_file


def initialize_git(project_path: str) -> tuple[bool, str]:
    return init_git(project_path)


def update_gitignore(project_path: str) -> tuple[bool, str]:
    gitignore_path = os.path.join(project_path, ".gitignore")
    
    lines_to_add = [
        "# Instrucciones para la IA",
        "*_instructions_*.txt",
        "*_instrucciones_*.txt",
        "",
        "# Carpeta de cambios de la app",
        "_changes/"
    ]
    
    if not os.path.exists(gitignore_path):
        with open(gitignore_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines_to_add))
        return True, "Gitignore creado"
    else:
        with open(gitignore_path, 'r', encoding='utf-8') as f:
            existing_content = f.read()
        
        needs_update = False
        for line in lines_to_add:
            if line and line not in existing_content:
                existing_content += "\n" + line
                needs_update = True
        
        if needs_update:
            with open(gitignore_path, 'w', encoding='utf-8') as f:
                f.write(existing_content)
            return True, "Gitignore actualizado"
    
    return True, "Gitignore sin cambios"


def initialize_project(project_path: str) -> tuple[bool, str, str]:
    success, msg = initialize_git(project_path)
    if not success:
        return False, msg, ""
    
    success, msg = update_gitignore(project_path)
    
    changes_file = create_changes_file(project_path)
    
    return True, f"Proyecto inicializado: {msg}", changes_file


def get_changes_file_path(project_path: str) -> str:
    return os.path.join(project_path, "_changes", "_changes.txt")


def ensure_project_structure(project_path: str) -> tuple[str, str]:
    create_changes_directory(project_path)
    changes_file = create_changes_file(project_path)
    return project_path, changes_file
