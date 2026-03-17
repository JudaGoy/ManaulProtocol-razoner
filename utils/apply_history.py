import os
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import List, Dict, Optional

MAX_VERSIONS = 15


def get_history_file_path(project_path: str, filename: str) -> str:
    changes_dir = os.path.join(project_path, "_changes")
    if not os.path.exists(changes_dir):
        os.makedirs(changes_dir, exist_ok=True)
    
    safe_filename = filename.replace("/", "_").replace("\\", "_").replace(":", "")
    return os.path.join(changes_dir, f"_{safe_filename}.txt")


def save_applied_code(project_path: str, filename: str, applied_code: str) -> bool:
    history_file = get_history_file_path(project_path, filename)
    
    changes = []
    
    if os.path.exists(history_file):
        try:
            tree = ET.parse(history_file)
            root = tree.getroot()
            for change_elem in root.findall("change"):
                date = change_elem.find("date")
                code = change_elem.find("code")
                if date is not None and code is not None:
                    changes.append({
                        "date": date.text or "",
                        "code": code.text or ""
                    })
        except Exception:
            changes = []
    
    new_change = {
        "date": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "code": applied_code
    }
    changes.append(new_change)
    
    if len(changes) > MAX_VERSIONS:
        changes = changes[-MAX_VERSIONS:]
    
    root = ET.Element("history")
    for change in changes:
        change_elem = ET.SubElement(root, "change")
        date_elem = ET.SubElement(change_elem, "date")
        date_elem.text = change["date"]
        code_elem = ET.SubElement(change_elem, "code")
        code_elem.text = change["code"]
    
    tree = ET.ElementTree(root)
    tree.write(history_file, encoding="utf-8", xml_declaration=True)
    
    return True


def get_apply_history(project_path: str, filename: str) -> List[Dict[str, str]]:
    history_file = get_history_file_path(project_path, filename)
    
    if not os.path.exists(history_file):
        return []
    
    changes = []
    
    try:
        tree = ET.parse(history_file)
        root = tree.getroot()
        for change_elem in root.findall("change"):
            date = change_elem.find("date")
            code = change_elem.find("code")
            if date is not None and code is not None:
                changes.append({
                    "date": date.text or "",
                    "code": code.text or ""
                })
    except Exception:
        return []
    
    return changes


def clear_apply_history(project_path: str, filename: str) -> bool:
    history_file = get_history_file_path(project_path, filename)
    
    if os.path.exists(history_file):
        os.remove(history_file)
    
    return True


def clear_all_apply_history(project_path: str) -> bool:
    changes_dir = os.path.join(project_path, "_changes")
    
    if not os.path.exists(changes_dir):
        return True
    
    for filename in os.listdir(changes_dir):
        if filename.startswith("_") and filename.endswith(".txt"):
            filepath = os.path.join(changes_dir, filename)
            try:
                os.remove(filepath)
            except Exception:
                pass
    
    return True


def get_files_with_history(project_path: str) -> List[str]:
    changes_dir = os.path.join(project_path, "_changes")
    
    if not os.path.exists(changes_dir):
        return []
    
    files = []
    for filename in os.listdir(changes_dir):
        if filename.startswith("_") and filename.endswith(".txt") and filename != "_changes.txt":
            original_name = filename[1:-4]
            files.append(original_name)
    
    return files
