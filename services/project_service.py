import os
import logging
from logging.handlers import RotatingFileHandler
from services.git_service import init_git, is_git_repo
from domain.prompt_generator import BINARY_EXTENSIONS
from domain.security import is_safe_path
from domain.models import ChangeError

LOG_FILE = "manual_protocol.log"
_logger = None


def setup_logging(project_path: str = "."):
    """Configura el sistema de logging con rotación."""
    global _logger
    if _logger is not None:
        return _logger
    
    log_path = os.path.join(project_path, LOG_FILE)
    
    _logger = logging.getLogger("manaul_protocol")
    _logger.setLevel(logging.INFO)
    
    handler = RotatingFileHandler(
        log_path,
        maxBytes=5*1024*1024,
        backupCount=3,
        encoding='utf-8'
    )
    formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    _logger.addHandler(handler)
    
    return _logger


def get_logger():
    """Retorna el logger configurado."""
    global _logger
    if _logger is None:
        _logger = setup_logging(".")
    return _logger


def log_session_start(project_path: str):
    """Registra el inicio de una sesión."""
    get_logger().info(f"Sesión iniciada en proyecto: {project_path}")


def log_session_end(applied: int, failed: int):
    """Registra el resumen final de la sesión."""
    get_logger().info(f"Sesión finalizada. Cambios aplicados: {applied}, Fallidos: {failed}")


def log_change_success(file_path: str, action: str):
    """Registra un cambio exitoso."""
    get_logger().info(f"[SUCCESS] {action.upper()}: {file_path}")


def log_change_error(file_path: str, action: str, error: ChangeError):
    """Registra un cambio fallido."""
    get_logger().error(
        f"[ERROR] {action.upper()}: {file_path} - "
        f"Tipo: {error.error_type} | Mensaje: {error.message}"
    )


def generate_error_report(error: ChangeError, raw_xml: str = "") -> str:
    suggerencias = {
        'error_coincidencia': 
            'El código de CODIGO_ANTIGUO no coincide exactamente con el archivo. Possible causas: (1) El archivo fue modificado, (2) La IA generó código con caracteres diferentes, (3) Diferencias de indentación. COPIA el código EXACTO del archivo.',
        'archivo_no_encontrado': 'El archivo en ARCHIVO no existe. Verifica la ruta.',
        'ruta_insegura': 'La ruta está fuera del directorio del proyecto.',
        'git_apply_fallo': 'El parche no puede aplicarse. Verifica que el código antiguo y nuevo sean correctos.',
        'old_code_vacio': 'CODIGO_ANTIGUO está vacío.',
        'bloque_demasiado_grande': 'El bloque es muy grande. Divide en cambios más pequeños.',
        'regex_error': 'Error al procesar el código.',
        'parser_error': 'El XML no puede parsearse. Verifica etiquetas y estructura.',
        'project_path_requerido': 'Falta la ruta del proyecto.',
        'aplicacion_fallo': 'El cambio no pudo aplicarse. La IA puede haber generado código incorrecto.',
        'excepcion_desconocida': 'Error inesperado.',
    }
    
    sugerencia = suggerencias.get(error.error_type, 'Revisa el contenido del cambio.')
    detail = error.detail if error.detail else "N/A"
    
    report = f"""
==================== ERROR DE APLICACIÓN ====================
{error.message}

📋 DETALLES:
- Tipo: {error.error_type}
- Archivo: {error.file_path}
- Detalle: {detail}

💡 SUGERENCIA:
{sugerencia}"""
    
    if raw_xml:
        raw_block = f"""
📄 BLOQUE XML QUE FALLÓ:
```
{raw_xml}
```

⚠️ Para solucionar, genera un nuevo cambio con:
1. Código EXACTO del archivo (copia y pega)
2. Ruta correcta en ARCHIVO
3. CODIGO_ANTIGUO exacto a reemplazar"""
        report += raw_block
    
    return report


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
        "_changes/",
        "",
        "# Archivos de sistema y caches",
        "__pycache__/",
        ".DS_Store",
        "",
        "# Archivos binarios y compilados",
    ]
    
    # Add binary extensions as patterns
    binary_patterns = sorted([f"*{ext}" for ext in BINARY_EXTENSIONS])
    lines_to_add.extend(binary_patterns)
    
    if not os.path.exists(gitignore_path):
        with open(gitignore_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines_to_add))
        return True, "Gitignore creado"
    else:
        with open(gitignore_path, 'r', encoding='utf-8') as f:
            existing_lines = {line.strip() for line in f.readlines()}
        
        to_append = []
        for line in lines_to_add:
            if line and line not in existing_lines:
                to_append.append(line)
        
        if to_append:
            with open(gitignore_path, 'a', encoding='utf-8') as f:
                f.write("\n" + "\n".join(to_append))
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
