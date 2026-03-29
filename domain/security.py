import os


def is_safe_path(base_path: str, target_path: str) -> bool:
    """
    Valida que target_path esté dentro de base_path.
    Previene path traversal attacks.
    """
    abs_base = os.path.abspath(base_path)
    abs_target = os.path.abspath(target_path)
    return abs_target.startswith(abs_base + os.sep) or abs_target == abs_base
