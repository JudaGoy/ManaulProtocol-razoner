import subprocess
import os
import tempfile
from datetime import datetime
from typing import List, Dict


def run_git_command(project_path: str, *args) -> tuple:
    try:
        env = os.environ.copy()
        env['GIT_TERMINAL_PROMPT'] = '0'
        
        result = subprocess.run(
            ["git", *args],
            cwd=project_path,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            env=env,
            timeout=10
        )
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except FileNotFoundError:
        return "", "Git no encontrado en el sistema", 1
    except subprocess.TimeoutExpired:
        return "", "El comando de Git excedió el tiempo de espera", 1
    except Exception as e:
        return "", str(e), 1


def is_git_repo(project_path: str) -> bool:
    git_dir = os.path.join(project_path, ".git")
    return os.path.isdir(git_dir)


def init_git(project_path: str) -> tuple[bool, str]:
    if is_git_repo(project_path):
        return True, "Git ya estaba inicializado"
    
    stdout, stderr, code = run_git_command(project_path, "init")
    
    if code == 0:
        return True, "Git inicializado correctamente"
    else:
        return False, f"Error al inicializar git: {stderr}"


def get_status(project_path: str) -> Dict[str, List[str]]:
    stdout, stderr, code = run_git_command(project_path, "status", "--porcelain")
    
    if code != 0:
        return {"staged": [], "modified": [], "untracked": []}
    
    staged = []
    modified = []
    untracked = []
    
    for line in stdout.split('\n'):
        if not line.strip():
            continue
        
        if len(line) >= 3:
            index_status = line[0]
            worktree_status = line[1]
            filepath = line[3:] if len(line) > 3 else line[2:].strip()
            
            if filepath.startswith('"') and filepath.endswith('"'):
                filepath = filepath[1:-1]
            
            if index_status in ('A', 'M', 'D', 'R', 'C') or worktree_status in ('M', 'D'):
                staged.append(filepath)
            
            if worktree_status in ('M', 'D'):
                modified.append(filepath)
            
            if index_status == '?' or worktree_status == '?':
                untracked.append(filepath)
    
    return {
        "staged": staged,
        "modified": modified,
        "untracked": untracked
    }


def get_history(project_path: str, limit: int = 50) -> List[Dict[str, str]]:
    separator = "||||"
    stdout, stderr, code = run_git_command(
        project_path, 
        "log", 
        f"--max-count={limit}",
        f"--pretty=format:%H{separator}%h{separator}%s{separator}%an{separator}%ad{separator}%cn{separator}%cd",
        "--date=format:%d/%m/%Y %H:%M:%S"
    )
    
    if code != 0 or not stdout:
        return []
    
    commits = []
    for line in stdout.split('\n'):
        if not line.strip():
            continue
        
        parts = line.split(separator)
        if len(parts) >= 6:
            commits.append({
                "hash": parts[0],
                "short_hash": parts[1],
                "message": parts[2],
                "author": parts[3],
                "author_date": parts[4],
                "committer": parts[5] if len(parts) > 5 else parts[3],
                "committer_date": parts[6] if len(parts) > 6 else parts[4]
            })
    
    return commits


def commit(project_path: str, message: str) -> tuple[bool, str]:
    stdout, stderr, code = run_git_command(project_path, "add", "-A")
    
    if code != 0:
        return False, f"Error al hacer git add: {stderr}"
    
    stdout, stderr, code = run_git_command(project_path, "commit", "-m", message)
    
    if code != 0:
        return False, f"Error al hacer commit: {stderr}"
    
    if "nothing to commit" in stdout.lower():
        return False, "No hay cambios para hacer commit"
    
    return True, f"Commit realizado: {message}"


def get_default_commit_message() -> str:
    now = datetime.now()
    return f"📝 {now.strftime('%d/%m/%Y %H:%M:%S')}"


def restore(project_path: str, commit_hash: str) -> tuple[bool, str]:
    stdout, stderr, code = run_git_command(project_path, "checkout", commit_hash, "--", ".")
    
    if code != 0:
        return False, f"Error al restaurar: {stderr}"
    
    return True, f"Restaurado al commit: {commit_hash[:8]}"


def get_commit_diff(project_path: str, commit_hash: str) -> str:
    stdout, stderr, code = run_git_command(
        project_path, 
        "show", 
        commit_hash, 
        "--pretty=format:", 
        "--no-color"
    )
    
    if code != 0:
        return f"Error al obtener diff: {stderr}"
    
    return stdout


def get_file_diff(project_path: str, file_path: str) -> str:
    stdout, stderr, code = run_git_command(
        project_path,
        "diff",
        "HEAD",
        "--",
        file_path
    )
    
    if code != 0:
        return f"Error al obtener diff: {stderr}"
    
    return stdout


def get_current_branch(project_path: str) -> str:
    stdout, stderr, code = run_git_command(project_path, "branch", "--show-current")
    
    if code != 0:
        return "main"
    
    return stdout or "main"


def get_commit_count(project_path: str) -> int:
    stdout, stderr, code = run_git_command(project_path, "rev-list", "--count", "HEAD")
    
    if code != 0 or not stdout:
        return 0
    
    try:
        return int(stdout)
    except ValueError:
        return 0


def get_file_at_commit(project_path: str, commit_hash: str, filename: str) -> str:
    filename = filename.replace("\\", "/")
    stdout, stderr, code = run_git_command(
        project_path,
        "show",
        f"{commit_hash}:{filename}"
    )
    
    if code != 0:
        return ""
    
    return stdout


def get_current_file_content(project_path: str, filename: str) -> str:
    filepath = os.path.join(project_path, filename)
    
    if not os.path.exists(filepath):
        return ""
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception:
        return ""


def revert_file(project_path: str, filename: str, commit_hash: str = None) -> tuple[bool, str]:
    target = "HEAD" if commit_hash is None else commit_hash
    
    stdout, stderr, code = run_git_command(project_path, "checkout", target, "--", filename)
    
    if code != 0:
        return False, f"Error al revertir: {stderr}"
    
    return True, f"Archivo revertido: {filename}"


def discard_all_changes(project_path: str) -> tuple[bool, str]:
    stdout, stderr, code = run_git_command(project_path, "checkout", "HEAD", "--", ".")
    
    if code != 0:
        return False, f"Error al descartar cambios: {stderr}"
    
    return True, "Todos los cambios descartados"


def get_commit_files(project_path: str, commit_hash: str) -> List[str]:
    stdout, stderr, code = run_git_command(
        project_path,
        "diff-tree",
        "--no-commit-id",
        "--name-only",
        "-r",
        commit_hash
    )
    
    if code != 0:
        return []
    
    if not stdout:
        return []
    
    return [f.strip() for f in stdout.split('\n') if f.strip()]


def get_modified_files_since_commit(project_path: str, commit_hash: str = "HEAD") -> List[str]:
    stdout, stderr, code = run_git_command(
        project_path,
        "diff",
        "--name-only",
        commit_hash
    )
    
    if code != 0:
        return []
    
    if not stdout:
        return []
    
    return [f.strip() for f in stdout.split('\n') if f.strip()]


def get_uncommitted_files(project_path: str) -> List[str]:
    modified = get_modified_files_since_commit(project_path, "HEAD")
    
    stdout, stderr, code = run_git_command(
        project_path,
        "ls-files",
        "--others",
        "--exclude-standard"
    )
    
    if code == 0 and stdout:
        untracked = [f.strip() for f in stdout.split('\n') if f.strip()]
    else:
        untracked = []
    
    return modified + untracked


def apply_git_patch(project_path: str, patch_content: str) -> tuple[bool, str]:
    tmp_path = ""
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.patch', delete=False, encoding='utf-8') as tmp:
            tmp.write(patch_content)
            tmp_path = tmp.name
        
        # Usamos --whitespace=fix para que git corrija automáticamente los problemas de espacios en blanco
        # que a veces genera la IA, lo cual causa los errores de "trailing whitespace" y "corrupt patch".
        # Esto es más robusto que --ignore-whitespace, que solo afecta la comparación.
        stdout, stderr, code = run_git_command(project_path, "apply", "--whitespace=fix", "--verbose", tmp_path)
        
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
            
        if code == 0:
            return True, f"Parche aplicado:\n{stdout}"
        else:
            return False, f"Error git apply: {stderr}"
            
    except Exception as e:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)
        return False, f"Excepción aplicando parche: {str(e)}"


def apply_patch_to_text(original_text: str, patch_content: str) -> str:
    import tempfile
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_file = os.path.join(temp_dir, "temp_file")
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write(original_text)
            
        success, msg = apply_git_patch(temp_dir, patch_content)
        
        if success:
            with open(temp_file, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            return original_text
