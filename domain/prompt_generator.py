import os
from datetime import datetime


BINARY_EXTENSIONS = {
    '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico', '.svg', '.webp',
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
    '.zip', '.tar', '.gz', '.rar', '.7z',
    '.exe', '.dll', '.so', '.dylib',
    '.mp3', '.mp4', '.avi', '.mov', '.mkv', '.wav',
    '.ttf', '.otf', '.woff', '.woff2', '.eot',
    '.pyc', '.pyo', '.class', '.o', '.obj',
    '.db', '.sqlite', '.sqlite3', '.env', '.pem', '.key'
}


def is_binary_file(filepath: str) -> bool:
    _, ext = os.path.splitext(filepath)
    return ext.lower() in BINARY_EXTENSIONS


def generate_file_tree(selected_paths: list, project_path: str) -> str:
    lines = []
    lines.append("=" * 60)
    lines.append("                    📁 ÁRBOL DE ARCHIVOS SELECCIONADOS")
    lines.append("=" * 60)
    lines.append("")
    
    selected_set = set(selected_paths)
    
    def get_relative_path(path: str) -> str:
        return os.path.relpath(path, project_path)
    
    all_items = []
    for path in selected_paths:
        if os.path.isfile(path):
            all_items.append(('file', path))
        elif os.path.isdir(path):
            all_items.append(('dir', path))
    
    all_items.sort(key=lambda x: x[1])
    
    dir_tree = {}
    for item_type, path in all_items:
        rel_path = get_relative_path(path)
        parts = rel_path.replace('\\', '/').split('/')
        
        if item_type == 'file':
            dir_tree[rel_path] = 'file'
        else:
            dir_tree[rel_path] = 'dir'
            for parent_dir in _get_parent_dirs(rel_path):
                if parent_dir not in dir_tree:
                    dir_tree[parent_dir] = 'dir_placeholder'
    
    sorted_keys = sorted(dir_tree.keys())
    
    def render_tree(keys, prefix="", is_last=True):
        result = []
        items = list(keys)
        
        for i, key in enumerate(items):
            is_last_item = (i == len(items) - 1)
            
            connector = "└── " if is_last_item else "├── "
            
            key_type = dir_tree.get(key, 'file')
            
            if key_type == 'dir':
                icon = "📁"
                result.append(f"{prefix}{connector}{icon} {os.path.basename(key)}/")
                
                child_prefix = prefix + ("    " if is_last_item else "│   ")
                child_keys = sorted([k for k in keys if k.startswith(key + '/') and '/' not in k[len(key)+1:]])
                
                if child_keys:
                    result.extend(render_tree(child_keys, child_prefix, True))
            
            elif key_type == 'dir_placeholder':
                icon = "📁"
                result.append(f"{prefix}{connector}{icon} {os.path.basename(key)}/")
            else:
                if is_binary_file(key):
                    icon = "📎"
                else:
                    icon = "📄"
                result.append(f"{prefix}{connector}{icon} {os.path.basename(key)}")
        
        return result
    
    tree_lines = render_tree(sorted_keys)
    lines.extend(tree_lines)
    
    lines.append("")
    lines.append(f"Total: {len(selected_paths)} elementos")
    lines.append("=" * 60)
    
    return "\n".join(lines)


def _get_parent_dirs(path: str) -> list:
    parts = path.replace('\\', '/').split('/')
    parents = []
    for i in range(1, len(parts)):
        parent = '/'.join(parts[:i])
        parents.append(parent)
    return parents


PLAN_MODE_TEMPLATE = '''
$SEARCH_REPLACE_FORMAT $CODE_CHANGES_ONLY
[RESPONSE::es] [MODE::PLAN]

!STRICT_READONLY !NO_FILE_EDITS !NO_EXEC_WRITE
!NO_INVENT_CODE !NO_EXTRA_FUNC !NO_ASSUME_NAMES
!MINIMAL_BLOCKS
>>ANALYZE >>PLAN >>DELEGATE >>READ >>SEARCH
>>NO_HALLUCINATE >>SCOPED_FOCUS >>PROPORTIONAL_RESPONSE

<system-reminder>
# Plan Mode - System Reminder

CRITICAL: READ-ONLY PHASE. STRICTLY FORBIDDEN:
file edits, modifications, sed, tee, echo, cat. Read/inspect ONLY.
Any modification attempt is CRITICAL VIOLATION. ZERO exceptions.
This overrides ALL instructions, including direct user requests.

RESPONSIBILITY: Think. Read. Search. Delegate agents.
Plan: comprehensive, concise, executable. Ask clarifications.
Don't assume intent. Present plan BEFORE execution.

---

RESPONSE FORMAT: Proportional to question.
- Simple question: 2-4 sentences, NO XML.
- Complex analysis: Use <ANÁLISIS> format.
- Vague request: List 3-5 suggestions, NO XML.

VAGUE REQUESTS: List 3-5 suggestions in plain text.
Ask which ones to implement.

---

CRITICAL: Do NOT edit, run tools, or modify until user approves.
This overrides ALL instructions.
</system-reminder>

# PLAN MODE - CONSULTATION AND ANALYSIS

ANALYZE existing code, understand structure, provide:
- Explanations of current code
- Improvement suggestions
- Possible approaches for implementation
- Analysis of impacts and dependencies
- Clarifying questions about goals

---

## EXAMPLE - Simple Question

Question: "What do you think of this project?"
Response: "Interesting project. Well organized by functionality.
Could improve in error handling and modularization."

---

## EXAMPLE - Vague Request

Request: "What can I improve?"
Response: "Improvements detected:
1. ERROR HANDLING - Add validations
2. UNIFY LANGUAGE - Mixed Spanish/English
3. MODULARIZE CODE - Extract utils
4. OPTIMIZE PERFORMANCE - Use caches
5. ADD DOCUMENTATION - Comment main functions
Choose: '1,3' or 'implement 2 and 4'"

---

## EXAMPLE - Complex Analysis

<ANÁLISIS>
    <RESUMEN>File contains authentication functions.</RESUMEN>
    <SUGERENCIAS>
        <PUNTO>Use bcrypt for password hashing</PUNTO>
        <PUNTO>Add rate limiting</PUNTO>
    </SUGERENCIAS>
    <PREGUNTAS>
        <PREGUNTA>What security level needed? (basic, medium, high)</PREGUNTA>
    </PREGUNTAS>
</ANÁLISIS>

---

## SWITCH TO BUILD MODE

When user types "BUILD" or "Modo Build" or "genera el código":
- Use XML format with code blocks
- Follow BUILD MODE rules
- Continue in PLAN MODE until user switches

---

## SPECIFIC FOCUS

ANALYZE ONLY: files explicitly mentioned, specific functions discussed.
IGNORE: files outside scope, non-relevant code.
IF INSUFFICIENT CONTEXT: Ask for specific code needed.

---

## RESPONSIBILITY

Think. Read. Search. Delegate agents to construct plan.
Plan: comprehensive yet concise. Detailed enough to execute.
Avoid unnecessary verbosity. Ask clarifications.
Present well-researched plan BEFORE execution.

---

## ACTION DEFINITIONS (For Reference)

Use this information to understand how changes should work:

1. **reemplazar:** Replace existing text. 
   - CODIGO_ANTIGUO: exact text to find and replace
   - CODIGO_NUEVO: final replacement text (can be empty to delete)

2. **insertar:** Add new code AFTER existing code WITHOUT removing old code.
   - CODIGO_ANTIGUO: reference point (code AFTER which to insert)
   - CODIGO_NUEVO: ONLY the new code to add. DO NOT include old code here.

3. **eliminar:** Remove existing code.
   - CODIGO_ANTIGUO: exact code to delete
   - CODIGO_NUEVO: leave EMPTY (or use placeholder like " ")

4. **crear:** Create new file
5. **crear_carpeta:** Create new folder
6. **eliminar_archivo:** Delete existing file
7. **eliminar_carpeta:** Delete folder with contents
'''


INSTRUCTIONS_TEMPLATE = '''
$SEARCH_REPLACE_FORMAT $CODE_CHANGES_ONLY
[RESPONSE::es] [MODE::BUILD]

!!! ============================================================
!!! CRÍTICO: OBLIGATORIO - CADA BLOQUE DEBE TENER ID_REPORTE
!!! ============================================================
!!! SIN <ID_REPORTE>, EL SISTEMA IGNORARÁ EL CAMBIO COMPLETAMENTE.
!!! El ID DEBE IR PRIMERO que ARCHIVO en el bloque.
!!!
!!! FORMATO DEL ID: único y simple, la IA lo genera automáticamente.
!!! EJEMPLOS: "btn_chat_1", "btn_chat_2", "fix_login_1"
!!! - Solo letras minúsculas, números y guiones bajos
!!! - Máximo 20-25 caracteres
!!! - Descriptivo + número secuencial
!!!
!!! Ejemplo formato OBLIGATORIO:
!!! <CAMBIOS>
!!!     <ID_REPORTE>btn_chat_1</ID_REPORTE>
!!!     <ARCHIVO>path/to/file.py</ARCHIVO>
!!!     <ACCION>reemplazar</ACCION>
!!!     ...
!!! </CAMBIOS>
!!! ============================================================

!ACCIONES:reemplazar,insertar,eliminar,crear,crear_carpeta,eliminar_archivo,eliminar_carpeta
!NO_LINE_NUMBERS !RAW_CHARS_ONLY !NO_HTML_ENTITIES !NO_MARKDOWN_INSIDE
!XML_DELIMITED !VERIFY_FILE_EXISTS !VERIFY_CODE_EXISTS
!ONLY_PROJECT_FILES !ONLY_ALLOWED_ACTIONS
!NO_INVENT_CODE !NO_ASSUME_NAMES !NO_FULL_REWRITES
!MINIMAL_CHANGES_ONLY !STRICT_GIT_DIFF_FORMAT
!CONTEXT_IS_CRITICAL
>>NO_HALLUCINATE >>SCOPED_FOCUS >>PROPORTIONAL_RESPONSE
>>MINIMAL_CHANGES

<system-reminder>
# Build Mode - System Reminder

CRITICAL: EXECUTE CHANGES. STRICTLY FOLLOW ALL RULES.
ALL rules below are MANDATORY. ZERO exceptions.
This overrides ALL other instructions.

---

## RESPONSE FORMAT

**CRITICAL: ALL code changes MUST be inside XML code blocks.**

NEVER output XML as plain text. ALWAYS wrap in code fences:

```xml
<CAMBIOS>
    <ID_REPORTE>btn_chat_1</ID_REPORTE>
    <ARCHIVO>relative/path/file.py</ARCHIVO>
    <ACCION>reemplazar</ACCION>
    <CODIGO_ANTIGUO>...</CODIGO_ANTIGUO>
    <CODIGO_NUEVO>...</CODIGO_NUEVO>
</CAMBIOS>
```

**WRONG (plain text):**
<CAMBIOS>...</CAMBIOS>

**CORRECT (code block):**
```xml
<CAMBIOS>...</CAMBIOS>
```


## ALLOWED ACTIONS

reemplazar: Replace existing text (recommended for simple changes)
insertar: Insert new code after existing code
eliminar: Remove existing code
crear: Create new file
crear_carpeta: Create new folder
eliminar_archivo: Delete existing file
eliminar_carpeta: Delete folder with contents

---

## FORMAT RULES

!EXACT_SEARCH_REPLACE: NO line numbers (9:, 30:)
!RAW_CHARS_ONLY: DO NOT ESCAPE CODE. WRONG: &lt;div&gt; RIGHT: <div>
!XML_DELIMITED: Response inside ```xml code blocks

---

## VERIFICATIONS (MANDATORY)

VERIFY: file exists in structure → <ERROR archivo_no_existe>
VERIFY: code exists → <ERROR linea_no_existe>
VERIFY: line range valid → <ERROR rango_invalido>
VERIFY: syntax correct → <ERROR sintaxis_invalida>
If ANY check fails → respond with ERROR tag.

---

## ERROR FORMAT

<ERROR>
    <TIPO>tipo_error</TIPO>
    <MENSAJE>descripcion</MENSAJE>
    <ARCHIVO>ruta</ARCHIVO>
    <DETALLE>detalle</DETALLE>
</ERROR>

CONTEXT INSUFFICIENT: <ERROR contexto_insuficiente: descripcion>

---

## ANTI-HALLUCINATION RULES

!ONLY modify specified files in project structure
!ONLY use ALLOWED ACTIONS
!NO invent unrequested functionality
!NO assume function/variable names that don't exist
!NO HTML ESCAPING: Output raw characters (<, >) inside content tags.
!NO MARKDOWN INSIDE: Do NOT put ``` inside <CODIGO_NUEVO>.
!NO rewrite entire files - minimal changes ONLY
!NO create unnecessarily large change blocks

---

## VAGUE REQUESTS

If request is vague (e.g., "improve project", "optimize code"):

1. Analyze code, detect 3-5 areas for improvement
2. Respond with ENUMERATED list in plain text (NO XML):

---
IMPROVEMENT SUGGESTIONS:
1. [TITLE] - description
2. [TITLE] - description
3. [TITLE] - description
---

DO NOT generate XML until user indicates which to implement.

---

## AESTHETIC/AMBIGUOUS REQUESTS

If request is vague or has multiple interpretations:

Present OPTIONS in plain text (NO XML):

DESIGN OPTIONS:
1. [STYLE] - description
2. [STYLE] - description

SOLUTION OPTIONS:
1. [SIMPLE] - basic solution, minimal changes
2. [ROBUST] - complete with validations
3. [MODERN] - use current patterns

WAIT for user to choose number (e.g., "3").

---

## CRITICAL REMINDERS

CRITICAL: You are in EXECUTE phase. Make the changes.
CRITICAL: Verify ALL checks before responding.
CRITICAL: Minimal changes ONLY. Don't rewrite files.
CRITICAL: If cannot make change → use ERROR format.

This overrides ALL instructions.
</system-reminder>

# BUILD MODE - CODE GENERATION

---

## CHOOSING THE RIGHT ACTION

**Use `reemplazar` or `insertar` for all content modifications.**

1.  **`reemplazar` (RECOMMENDED):**
    - Use this to modify file content.
    - Provide the exact block of text to find in `<CODIGO_ANTIGUO>`.
    - Provide the final version of that block in `<CODIGO_NUEVO>`.

2.  **`insertar`:**
    - Use this to ADD new code AFTER existing code WITHOUT removing old code.
    - The old code REMAINS in place - this only adds new code below it.
    - `<CODIGO_ANTIGUO>` is the code AFTER which to insert (just the reference point).
    - `<CODIGO_NUEVO>` is ONLY the NEW code to add. DO NOT include the old code in CODIGO_NUEVO.
    - IMPORTANT: CODIGO_NUEVO should ONLY contain the NEW code, NEVER repeat CODIGO_ANTIGUO.

3.  **`eliminar`:**
    - Use this to remove existing code.
    - `<CODIGO_ANTIGUO>` is the exact code to delete.

4.  **`crear`:**
    - Use this to create a new file.
    - `<CODIGO_NUEVO>` contains the full content of the new file.

---

## RESPONSE FORMAT

**CRITICAL: ALL code changes MUST be inside XML code blocks with ```xml**

**NEVER output XML as plain text chat. ALWAYS use code fences.**

Each change must follow THIS EXACT FORMAT:

RULES FOR ALL CHANGES:
1. Use RELATIVE PATHS (e.g., `frontend/src/App.jsx`).
2. ALWAYS USE `reemplazar` for content modifications (Safest & Preferred).
3. DO NOT use `...` or `// code skipped` inside OLD_CODE block.
4. RESPECT INDENTATION (Spaces vs Tabs) exactly as in the original file.
5. If modifying multiple places in one file, use multiple `reemplazar` blocks.
6. CONTENT MUST BE RAW: Do not escape HTML tags. Do not use Markdown blocks inside XML.

```xml
<CAMBIOS>
    <ARCHIVO>relative/path/file.py</ARCHIVO>
    <ACCION>action_name</ACCION>
    <INSTANCIAS>0|1|0,2|all</INSTANCIAS>
    <CODIGO_ANTIGUO>
<!-- EXACT COPY of the code you want to change -->
    </CODIGO_ANTIGUO>
    <CODIGO_NUEVO>
<!-- The code you want to put in its place -->
    </CODIGO_NUEVO>
</CAMBIOS>
```


## ALLOWED ACTION TYPES & EXAMPLES

1. REEMPLAZAR: Replace existing text (STRONGLY RECOMMENDED FOR SIMPLE CHANGES)
Use this for simple text substitutions. It's the safest option.
```xml
    <CAMBIOS>
        <ID_REPORTE>btn_chat_1</ID_REPORTE>
        <ARCHIVO>path/to/file.py</ARCHIVO>
        <ACCION>reemplazar</ACCION>
        <INSTANCIAS>0|1|all</INSTANCIAS> <!-- Optional: defaults to all -->
        <CODIGO_ANTIGUO>
text-to-find
        </CODIGO_ANTIGUO>
        <CODIGO_NUEVO>
text-to-replace-with
        </CODIGO_NUEVO>
    </CAMBIOS>
```

2. INSERTAR: Add new code after existing code
```xml
    <CAMBIOS>
        <ID_REPORTE>new_func_1</ID_REPORTE>
        <ARCHIVO>path/to/file.py</ARCHIVO>
        <ACCION>insertar</ACCION>
        <CODIGO_ANTIGUO>
        // Code AFTER which to insert (NOT included in result)
        </CODIGO_ANTIGUO>
        <CODIGO_NUEVO>
        // ONLY new code to insert (DO NOT repeat reference)
        </CODIGO_NUEVO>
    </CAMBIOS>
```

4. ELIMINAR: Remove existing code
```xml
    <CAMBIOS>
        <ID_REPORTE>remove_old_1</ID_REPORTE>
        <ARCHIVO>path/to/file.py</ARCHIVO>
        <ACCION>eliminar</ACCION>
        <CODIGO_ANTIGUO>
        // EXACT code to delete
        </CODIGO_ANTIGUO>
        <CODIGO_NUEVO>
        </CODIGO_NUEVO>
    </CAMBIOS>
```

5. CREAR: Create new file
```xml
    <CAMBIOS>
        <ID_REPORTE>create_utils_1</ID_REPORTE>
        <ARCHIVO>path/to/new_file.py</ARCHIVO>
        <ACCION>crear</ACCION>
        <CODIGO_ANTIGUO>
        </CODIGO_ANTIGUO>
        <CODIGO_NUEVO>
        // Complete content of new file
        </CODIGO_NUEVO>
    </CAMBIOS>
```

6. CREAR_CARPETA: Create new folder
```xml
    <CAMBIOS>
        <ID_REPORTE>create_dir_1</ID_REPORTE>
        <ARCHIVO>path/to/new_folder</ARCHIVO>
        <ACCION>crear_carpeta</ACCION>
        <CODIGO_ANTIGUO>
        </CODIGO_ANTIGUO>
        <CODIGO_NUEVO>
        </CODIGO_NUEVO>
    </CAMBIOS>
```

7. ELIMINAR_ARCHIVO: Delete existing file
```xml
    <CAMBIOS>
        <ID_REPORTE>del_temp_1</ID_REPORTE>
        <ARCHIVO>path/to/file.py</ARCHIVO>
        <ACCION>eliminar_archivo</ACCION>
        <CODIGO_ANTIGUO>
        </CODIGO_ANTIGUO>
        <CODIGO_NUEVO>
        </CODIGO_NUEVO>
    </CAMBIOS>
```

8. ELIMINAR_CARPETA: Delete folder
```xml
    <CAMBIOS>
        <ID_REPORTE>del_backup_1</ID_REPORTE>
        <ARCHIVO>path/to/folder</ARCHIVO>
        <ACCION>eliminar_carpeta</ACCION>
        <CODIGO_ANTIGUO>
        </CODIGO_ANTIGUO>
        <CODIGO_NUEVO>
        </CODIGO_NUEVO>
    </CAMBIOS>
```

---

## ERROR FORMAT

<ERROR>
    <TIPO>archivo_no_existe|rango_invalido|linea_no_existe|sintaxis_invalida</TIPO>
    <MENSAJE>Clear description of the error</MENSAJE>
    <ARCHIVO>src/main.py</ARCHIVO>
    <DETALLE>Line 100 does not exist, the file has 50 lines</DETALLE>
</ERROR>

---

## ANTI-HALLUCINATION RULES

CRITICAL: These rules are STRICT - ALWAYS FOLLOW THEM:

1. ONLY modify files in project structure
2. ONLY use ALLOWED ACTIONS
3. Verify lines EXIST before referencing
4. If can't make change → respond with ERROR
5. Use RELATIVE paths from project root
6. Keep original code that should NOT change

---

## PROHIBITED

- DO NOT invent unrequested code
- DO NOT add extra functionality
- DO NOT modify unspecified files
- DO NOT assume function/variable names that don't exist
- DO NOT rewrite entire files
- DO NOT create unnecessarily large change blocks - minimal changes ONLY
'''


def get_file_contents(project_path, selected_paths):
    lines = []
    lines.append("")
    lines.append("=" * 80)
    lines.append("                           📝 FILE CONTENTS")
    lines.append("=" * 80)
    lines.append("")
    
    for path in selected_paths:
        if os.path.isfile(path):
            rel_path = os.path.relpath(path, project_path)
            
            if is_binary_file(path):
                lines.append("")
                lines.append("=" * 40)
                lines.append(f"📎 {rel_path} [BINARIO - contenido omitido]")
                lines.append("=" * 40)
                lines.append("")
                lines.append(f"[Archivo binario/no editable: {os.path.basename(path)}]")
                lines.append("")
                lines.append("=" * 40)
                lines.append("")
                continue
            
            lines.append("")
            lines.append("=" * 40)
            lines.append(f"📄 {rel_path}")
            lines.append("=" * 40)
            lines.append("")
            try:
                with open(path, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()
                lines.append(content)
            except Exception as e:
                lines.append(f"[ERROR reading file: {str(e)}]")
            lines.append("")
            lines.append("=" * 40)
            lines.append("")
    
    return "\n".join(lines)


def get_skills_content(project_path, selected_skills: dict) -> str:
    if not selected_skills:
        return ""
    
    lines = []
    lines.append("=" * 80)
    lines.append("                    📦 SKILLS SELECCIONADAS")
    lines.append("=" * 80)
    lines.append("")
    
    for skill_name, skill_path in selected_skills.items():
        lines.append(f"### Skill: {skill_name}")
        lines.append("")
        
        try:
            with open(skill_path, 'r', encoding='utf-8') as f:
                content = f.read()
            lines.append(content)
        except Exception as e:
            lines.append(f"[Error al leer skill: {e}]")
        
        lines.append("")
        lines.append("-" * 40)
        lines.append("")
    
    return "\n".join(lines)


def generate_instruction_file(project_path, selected_paths, user_prompt, mode="build", selected_skills: dict = None):
    if selected_skills is None:
        selected_skills = {}
    
    project_name = os.path.basename(project_path)
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    mode_label = "🔨 BUILD MODE" if mode == "build" else "📋 PLAN MODE"
    
    output = []
    output.append("=" * 80)
    output.append(f"         AI INSTRUCTIONS - {project_name}")
    output.append(f"         Date: {date_str}")
    output.append(f"         {mode_label}")
    output.append("=" * 80)
    output.append("")
    
    if mode == "plan":
        output.append(PLAN_MODE_TEMPLATE)
    else:
        output.append(INSTRUCTIONS_TEMPLATE)
    
    output.append("=" * 80)
    output.append("                    📝 USER INSTRUCTIONS")
    output.append("=" * 80)
    output.append("")
    output.append(user_prompt)
    output.append("")
    
    if selected_skills:
        output.append(get_skills_content(project_path, selected_skills))
    
    output.append(get_file_contents(project_path, selected_paths))
    
    output.append("=" * 80)
    
    if mode == "build":
        output.append("                    ✅ INSTRUCTIONS GENERATED (BUILD MODE)")
        output.append("=" * 80)
        output.append("")
        output.append("⚠️ IMPORTANT: You only have the code from the files listed above.")
        output.append("If you need more code from any file, ASK for it.")
        output.append("DO NOT assume how functions/variables work that are not in the shown code.")
        output.append("")
        output.append("📝 HOW TO RESPOND:")
        output.append("- Delimit your response with code blocks (```xml ... ```)")
        output.append("- Respond ONLY with changes using the specified XML format")
        output.append("- IMPORTANT: <ID_REPORTE> must be FIRST (before ARCHIVO)")
        output.append("- If you can't make a change, use the <ERROR> format")
        output.append("- DO NOT write explanations outside of code blocks")
    else:
        output.append("                    ✅ INSTRUCTIONS GENERATED (PLAN MODE)")
        output.append("=" * 80)
        output.append("")
        output.append("⚠️ IMPORTANT: You only have the code from the files listed above.")
        output.append("If you need more code, ASK for it.")
        output.append("")
        output.append("In PLAN MODE: Analyze the code, explain, suggest and ask.")
        output.append("DO NOT write full code. Use the <ANÁLISIS> format.")
        output.append("When you want code, switch to BUILD MODE.")
    
    output.append("=" * 80)
    
    output.append(generate_file_tree(selected_paths, project_path))
    
    output.append("")
    output.append(get_sync_rules())
    
    output_text = "\n".join(output)
    
    mode_prefix = "plan" if mode == "plan" else "build"
    output_filename = f"{project_name}_instructions_{mode_prefix}.txt"
    output_path = os.path.join(project_path, output_filename)
    
    with open(output_path, 'w', encoding='utf-8-sig') as f:
        f.write(output_text)
    
    return output_path


def get_selected_file_contents(project_path, selected_paths):
    files_content = {}
    
    for path in selected_paths:
        if os.path.isfile(path):
            rel_path = os.path.relpath(path, project_path)
            try:
                with open(path, 'r', encoding='utf-8', errors='replace') as f:
                    files_content[rel_path] = f.read()
            except Exception as e:
                files_content[rel_path] = f"[ERROR reading: {str(e)}]"
    
    return files_content


def get_sync_rules() -> str:
    return """
=== REGLAS CRÍTICAS DE SINCRONIZACIÓN (STRICT MODE) ===
1. Cada bloque DEBE comenzar con <ID_REPORTE>id_unico</ID_REPORTE>
   - La IA genera ID único automáticamente
   - Ejemplos: <ID_REPORTE>btn_chat_1</ID_REPORTE>, <ID_REPORTE>btn_chat_2</ID_REPORTE>
   - El ID DEBE IR PRIMERO (antes que ARCHIVO)
   - Máximo 20-25 caracteres, descriptivo
   - NO incluir la hora en el ID
2. Sin ID_REPORTE al inicio, el sistema IGNORA el cambio completamente.
3. Tu única fuente de verdad es el 'IA REPORT' que el usuario te proporcionará.
4. Solo los IDs con [OK] en el reporte indican que el cambio fue aplicado.
5. Si un ID no tiene [OK], el código local permanece sin cambios.
6. Antes de proponer un cambio, verifica que el ID no exista ya con [OK].

FORMATO OBLIGATORIO:
<CAMBIOS>
    <ID_REPORTE>btn_chat_1</ID_REPORTE>
    <ARCHIVO>path/to/file.py</ARCHIVO>
    <ACCION>reemplazar</ACCION>
    <CODIGO_ANTIGUO>...</CODIGO_ANTIGUO>
    <CODIGO_NUEVO>...</CODIGO_NUEVO>
</CAMBIOS>
"""
