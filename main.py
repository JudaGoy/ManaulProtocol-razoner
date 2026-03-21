import customtkinter as ctk
from tkinter import filedialog
import os
import tkinter as tk
from tkinter import ttk
from tkinter import font

from utils.file_watcher import ProjectWatcher

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class AICodeEditor(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("AI Code Editor")
        self.geometry("1200x800")
        
        self.project_path = None
        self.changes_path = None
        self.selected_files = {}
        self.item_sizes = {}
        self.folder_selected_sizes = {}
        self.file_tree_items = {}
        self.current_mode = "build"  # "plan" or "build"
        
        self.setup_ui()
    
    def setup_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        self.sidebar = ctk.CTkFrame(self, width=250, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        self.main_content = ctk.CTkFrame(self)
        self.main_content.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        
        self.setup_sidebar()
        self.setup_main_content()
    
    def setup_sidebar(self):
        title_label = ctk.CTkLabel(
            self.sidebar, 
            text="AI Code Editor",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=(20, 5))
        
        self.mode_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.mode_frame.pack(pady=5, padx=20, fill="x")
        
        ctk.CTkLabel(
            self.mode_frame,
            text="Modo:",
            font=ctk.CTkFont(size=12)
        ).pack(side="left", padx=5)
        
        self.mode_switch = ctk.CTkSegmentedButton(
            self.mode_frame,
            values=["📋 Plan", "🔨 Build"],
            command=self.on_mode_change,
            selected_color="#3B8ED0"
        )
        self.mode_switch.set("🔨 Build")
        self.mode_switch.pack(side="left", padx=5)
        
        self.lbl_mode_info = ctk.CTkLabel(
            self.sidebar,
            text="💡 Build: La IA da código directamente",
            wraplength=200,
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        self.lbl_mode_info.pack(pady=(0, 10))
        
        self.btn_select_project = ctk.CTkButton(
            self.sidebar,
            text="📁 Seleccionar Proyecto",
            command=self.select_project,
            height=40
        )
        self.btn_select_project.pack(pady=10, padx=20, fill="x")
        
        self.lbl_project = ctk.CTkLabel(
            self.sidebar,
            text="Ningún proyecto seleccionado",
            wraplength=200,
            font=ctk.CTkFont(size=12)
        )
        self.lbl_project.pack(pady=10, padx=20)
        
        separator = ctk.CTkFrame(self.sidebar, height=2)
        separator.pack(pady=20, padx=20, fill="x")
        
        self.btn_generate = ctk.CTkButton(
            self.sidebar,
            text="📝 Generar Instrucciones",
            command=self.generate_instructions,
            height=40,
            state="disabled"
        )
        self.btn_generate.pack(pady=10, padx=20, fill="x")
        
        self.btn_apply = ctk.CTkButton(
            self.sidebar,
            text="📂 Gestionar Cambios",
            command=self.manage_changes,
            height=40,
            state="disabled"
        )
        self.btn_apply.pack(pady=10, padx=20, fill="x")
        
    
    def setup_main_content(self):
        self.main_content.grid_columnconfigure(0, weight=1)
        self.main_content.grid_rowconfigure(1, weight=1)
        
        self.lbl_title = ctk.CTkLabel(
            self.main_content,
            text="Selecciona un proyecto para comenzar",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        self.lbl_title.grid(row=0, column=0, pady=10, padx=10, sticky="w")
        
        self.file_frame = ctk.CTkFrame(self.main_content)
        self.file_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self.file_frame.grid_rowconfigure(0, weight=1)
        self.file_frame.grid_columnconfigure(0, weight=1)
        
        self.prompt_frame = ctk.CTkFrame(self.main_content, height=200)
        self.prompt_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=5)
        self.prompt_frame.grid_columnconfigure(0, weight=1)
        
        self.lbl_prompt = ctk.CTkLabel(
            self.prompt_frame,
            text="📝 Instrucciones para la IA:",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.lbl_prompt.grid(row=0, column=0, pady=(10,5), padx=10, sticky="w")
        
        self.txt_prompt = ctk.CTkTextbox(self.prompt_frame, height=150)
        self.txt_prompt.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        
        self.create_file_browser()
    
    def create_file_browser(self):
        style = ttk.Style()
        # Usamos 'clam' para tener control total sobre los colores y bordes
        style.theme_use("clam")

        style.configure(
            "Treeview",
            background="#2B2B2B",
            foreground="white",
            fieldbackground="#2B2B2B", # Esto evita que el fondo se ponga blanco
            rowheight=28,
            font=("Consolas", 11),
            borderwidth=0,
        )
        style.configure(
            "Treeview.Heading",
            background="#1F1F1F",
            foreground="white",
            font=("Consolas", 11, "bold"),
            borderwidth=0
        )
        # Eliminar el borde de enfoque (focus highlight) en el tema clam
        style.layout("Treeview", [('Treeview.treearea', {'sticky': 'nswe'})])
        
        style.map("Treeview", background=[("selected", "#3B8ED0")])
        
        self.tree_frame = ctk.CTkFrame(self.file_frame, fg_color="#2B2B2B", border_width=0)
        self.tree_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.tree_frame.grid_columnconfigure(0, weight=1)
        self.tree_frame.grid_rowconfigure(0, weight=1)
        
        self.tree = ttk.Treeview(
            self.tree_frame, 
            show="tree", 
            selectmode="browse",
            style="Treeview"
        )
        self.tree.grid(row=0, column=0, sticky="nsew")
        
        scrollbar = ctk.CTkScrollbar(self.tree_frame, orientation="vertical", command=self.tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)
        self.tree.bind("<Button-1>", self.on_tree_click)
        
        # Configurar etiqueta para resaltar en rojo archivos pesados
        self.tree.tag_configure("large_file", foreground="#FF5555")
    
    def select_project(self):
        folder = filedialog.askdirectory(title="Seleccionar Proyecto")
        if folder:
            self.project_path = folder
            self.lbl_project.configure(text=f"Proyecto:\n{os.path.basename(folder)}")
            self.lbl_title.configure(text=f"Archivos del proyecto: {os.path.basename(folder)}")
            self.load_project_files(folder)
            
            changes_folder = os.path.join(folder, "_changes")
            if not os.path.exists(changes_folder):
                os.makedirs(changes_folder, exist_ok=True)
            
            changes_file = os.path.join(changes_folder, "_changes.txt")
            if not os.path.exists(changes_file):
                with open(changes_file, 'w', encoding='utf-8') as f:
                    f.write("")
            
            self.btn_generate.configure(state="normal")
            self.btn_apply.configure(state="normal")
            
            from utils.git_manager import init_git
            success, msg = init_git(self.project_path)
            print(f"Git: {msg}")
            
            gitignore_path = os.path.join(self.project_path, ".gitignore")
            
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
                print("Gitignore creado")
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
                    print("Gitignore actualizado")
            
            self.current_folder = folder
            
            if hasattr(self, 'watcher') and self.watcher:
                self.watcher.detener()
            
            self.watcher = ProjectWatcher(folder, self.on_new_item_created, self.on_git_commit)
            self.watcher.iniciar()
    
    def manage_changes(self):
        if not self.project_path:
            self.show_error("Selecciona un proyecto primero")
            return
        
        changes_file = os.path.join(self.project_path, "_changes", "_changes.txt")
        
        if not os.path.exists(os.path.dirname(changes_file)):
            os.makedirs(os.path.dirname(changes_file), exist_ok=True)
        
        if not os.path.exists(changes_file):
            with open(changes_file, 'w', encoding='utf-8') as f:
                f.write("")
        
        from ui.gestionar_cambios import GestionarCambiosWindow
        win = GestionarCambiosWindow(self, self.project_path, changes_file)
        win.lift()
        win.focus_force()
    
    def format_size(self, size):
        if size < 1024 * 1024:
            size_in_kb = size / 1024
            return f"{size_in_kb:.2f} KB"
        size_in_mb = size / (1024 * 1024)
        return f"{size_in_mb:.2f} MB"

    def load_project_files(self, folder):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.selected_files = {}
        self.item_sizes = {}
        self.folder_selected_sizes = {}
        self.file_tree_items = {}
        
        root_item = self.tree.insert(
            "", 
            "end", 
            open=True,
            values=(folder, "directory", True)
        )
        self.file_tree_items[folder] = root_item
        self.selected_files[folder] = True
        
        total_size = self.add_folder_contents(folder, root_item)
        self.item_sizes[folder] = total_size
        self.folder_selected_sizes[folder] = total_size
        self.update_folder_appearance(root_item)
        
        for item_id in self.tree.get_children(root_item):
            self.tree.item(item_id, open=True)
    
    def add_folder_contents(self, folder, parent_item):
        total_size = 0
        try:
            items = sorted(os.listdir(folder))
        except PermissionError:
            return 0
        
        dirs = []
        files = []
        
        for item in items:
            if item.startswith('.'):
                continue
            if '_instrucciones_' in item or '_instructions_' in item:
                continue
            if item == '_changes':
                continue
            path = os.path.join(folder, item)
            if os.path.isdir(path):
                dirs.append(item)
            else:
                files.append(item)
        
        for dirname in dirs:
            path = os.path.join(folder, dirname)
            dir_item = self.tree.insert(
                parent_item, 
                "end", 
                text=f"☑️ 📁 {dirname}",
                values=(path, "directory", True),
                tags=("directory",)
            )
            self.file_tree_items[path] = dir_item
            self.selected_files[path] = True
            dir_size = self.add_folder_contents(path, dir_item)
            total_size += dir_size
            self.item_sizes[path] = dir_size
            self.folder_selected_sizes[path] = dir_size
            self.update_folder_appearance(dir_item)
        
        for filename in files:
            path = os.path.join(folder, filename)
            try:
                size = os.path.getsize(path)
            except OSError:
                size = 0
            total_size += size
            self.item_sizes[path] = size
            
            file_text = f"☑️ 📄 {filename}\t({self.format_size(size)})"
            file_tags = ("file",)
            if size > 500 * 1024:  # Advertencia archivo > 500KB (Más realista para código)
                file_text += " ⚠️"
                file_tags = ("file", "large_file")
                
            file_item = self.tree.insert(
                parent_item,
                "end",
                text=file_text,
                values=(path, "file", True),
                tags=file_tags
            )
            self.file_tree_items[path] = file_item
            self.selected_files[path] = True
            
        return total_size
    
    def on_new_item_created(self):
        if not hasattr(self, 'watcher') or not self.watcher:
            return
        if self.watcher.ignorar:
            return
        self.refresh_tree(select_new=True)
    
    def refresh_tree(self, select_new=False):
        current_folder = getattr(self, 'current_folder', None)
        if not current_folder:
            return
        
        old_items = set(self.file_tree_items.keys())
        
        self.load_project_files(current_folder)
        
        if not select_new:
            return
        
        new_items = set(self.file_tree_items.keys())
        added_items = new_items - old_items
        
        if added_items:
            for new_path in sorted(added_items):
                if new_path in self.file_tree_items:
                    item = self.file_tree_items[new_path]
                    self.tree.selection_add(item)
            
            for new_path in added_items:
                parent = os.path.dirname(new_path)
                while parent and parent != current_folder:
                    if parent in self.file_tree_items:
                        self.tree.item(self.file_tree_items[parent], open=True)
                    parent = os.path.dirname(parent)
            
            first_item = self.file_tree_items[sorted(added_items)[0]]
            self.tree.see(first_item)
    
    def on_git_commit(self, files):
        if not files:
            return
        
        from utils.apply_history import clear_history_for_files
        
        full_paths = []
        for filename in files:
            full_path = os.path.join(self.project_path, filename)
            if os.path.exists(full_path):
                full_paths.append(full_path)
        
        if full_paths:
            clear_history_for_files(self.project_path, full_paths)
            print(f"Historial de cambios limpiado para {len(full_paths)} archivos en commit")
    
    def detener_watcher(self):
        if hasattr(self, 'watcher') and self.watcher:
            self.watcher.detener()
            self.watcher = None
    
    def on_tree_select(self, event):
        pass
    
    def on_tree_click(self, event):
        # Identify the specific element under the cursor (e.g., indicator, text)
        element = self.tree.identify_element(event.x, event.y)

        # If the click is on the expand/collapse arrow ('indicator'), we do nothing.
        # This allows the default Treeview behavior to handle expanding/collapsing.
        if "indicator" in str(element):
            return

        # Now, identify the item row that was clicked.
        item_id = self.tree.identify_row(event.y)
        if not item_id:
            return

        # We only want to proceed if the click was on the item's text area.
        # This prevents toggling when clicking on empty space in the row.
        if "text" in str(element):
            # Get the bounding box for the entire content of the item in the tree column.
            # bbox[0] is the starting x-coordinate, which includes indentation.
            bbox = self.tree.bbox(item_id, '#0')
            if not bbox:
                return

            item_content_start_x = bbox[0]

            # --- KEY HEURISTIC ---
            # The Treeview reserves space for an indicator arrow even for leaf nodes (files).
            # This space is to the left of the icon/text. We need to account for this offset.
            # A value of 20 pixels is a reliable estimate for this reserved space.
            INDICATOR_SPACE_WIDTH = 20

            # The actual visual text (and our checkbox) starts after the indentation and this reserved space.
            text_visual_start_x = item_content_start_x + INDICATOR_SPACE_WIDTH

            # Define a clickable width for our checkbox character.
            CHECKBOX_AREA_WIDTH = 25

            # Check if the click's x-coordinate falls within the calculated checkbox area.
            if text_visual_start_x <= event.x < text_visual_start_x + CHECKBOX_AREA_WIDTH:
                self.toggle_selection(item_id)
                # Return "break" to stop the event. This is crucial to prevent tkinter's
                # default row selection behavior from firing, which would interfere.
                return "break"
    
    def toggle_selection(self, item_id):
        values = self.tree.item(item_id, 'values')
        if not values:
            return 
        
        path, item_type, _ = values
        
        # Obtener el estado actual
        is_currently_selected = self.selected_files.get(path, False)
        new_selected_state = not is_currently_selected
        self.selected_files[path] = new_selected_state

        # Actualizar visualmente el checkbox del item clickeado
        current_text = self.tree.item(item_id, 'text')
        if new_selected_state:
            new_text = current_text.replace("⬜", "☑️")
        else:
            new_text = current_text.replace("☑️", "⬜")
        self.tree.item(item_id, text=new_text)

        delta = 0
        
        if item_type == "directory":
            # Lógica precisa para carpetas:
            # Delta = (Peso objetivo) - (Peso seleccionado actual)
            # Si seleccionamos: el objetivo es el peso total de la carpeta.
            # Si deseleccionamos: el objetivo es 0.
            total_size = self.item_sizes.get(path, 0)
            current_selected = self.folder_selected_sizes.get(path, 0)
            
            if new_selected_state:
                target_size = total_size
            else:
                target_size = 0
            
            delta = target_size - current_selected
            self.folder_selected_sizes[path] = target_size
            
            # Propagar el estado a todos los hijos
            self.update_children_selection(item_id, new_selected_state)
            
            self.update_folder_appearance(item_id)
        
        else:
            # Lógica para archivos individuales
            file_size = self.item_sizes.get(path, 0)
            if new_selected_state:
                delta = file_size
            else:
                delta = -file_size
        
        # Propagar la diferencia (delta) calculada hacia arriba
        self.update_parent_folders(item_id, delta)

    def update_parent_folders(self, item_id, delta):
        """Sube por el árbol actualizando el tamaño seleccionado y la apariencia de cada padre."""
        parent_id = self.tree.parent(item_id)
        while parent_id:
            parent_values = self.tree.item(parent_id, 'values')
            if not parent_values:
                break
            
            parent_path = parent_values[0]
            if parent_path in self.folder_selected_sizes:
                self.folder_selected_sizes[parent_path] += delta
                self.update_folder_appearance(parent_id)
            
            parent_id = self.tree.parent(parent_id)

    def update_folder_appearance(self, item_id):
        """Actualiza el texto y las etiquetas de una carpeta según su tamaño seleccionado."""
        values = self.tree.item(item_id, 'values')
        if not values: return
        path, _, _ = values
        is_selected = self.selected_files.get(path, False)
        total_size = self.item_sizes.get(path, 0)
        selected_size = self.folder_selected_sizes.get(path, 0)
        checkbox = "☑️" if is_selected else "⬜"
        basename = os.path.basename(path)
        text = f"{checkbox} 📁 {basename}\t({self.format_size(selected_size)})"
        tags = ("directory",)
        if selected_size > 2 * 1024 * 1024:  # Advertencia carpeta acumulada > 2MB
            text += " ⚠️"
            tags = ("directory", "large_file")
        self.tree.item(item_id, text=text, tags=tags)

    def update_children_selection(self, parent_item, selected):
        children = self.tree.get_children(parent_item)
        for child in children:
            child_values = self.tree.item(child, 'values')
            if child_values:
                child_path = child_values[0]
                self.selected_files[child_path] = selected
                
                # Si el hijo es una carpeta, debemos forzar su peso seleccionado interno
                # para que coincida con el estado 'selected' (todo o nada)
                child_type = child_values[1]
                if child_type == "directory":
                    total = self.item_sizes.get(child_path, 0)
                    self.folder_selected_sizes[child_path] = total if selected else 0
                    self.update_folder_appearance(child)
                
                child_text = self.tree.item(child, 'text')
                if selected:
                    new_text = child_text.replace("⬜", "☑️")
                else:
                    new_text = child_text.replace("☑️", "⬜")
                self.tree.item(child, text=new_text)
                
                self.update_children_selection(child, selected)
    
    def on_mode_change(self, value):
        if "Plan" in value:
            self.current_mode = "plan"
            self.lbl_mode_info.configure(
                text="💡 Plan: Consulta con IA sin dar código\nLuego cambia a Build para obtener código",
                text_color="#FFD700"
            )
        else:
            self.current_mode = "build"
            self.lbl_mode_info.configure(
                text="💡 Build: La IA da código directamente",
                text_color="gray"
            )
    
    def generate_instructions(self):
        from core.prompt_generator import generate_instruction_file
        
        prompt = self.txt_prompt.get("1.0", "end-1c")
        
        selected_paths = [path for path, selected in self.selected_files.items() if selected]
        
        if not selected_paths:
            self.show_error("No hay archivos seleccionados")
            return
        
        if not prompt.strip():
            self.show_error("Por favor escribe las instrucciones para la IA")
            return
        
        changes_folder = os.path.join(self.project_path, "_changes")
        if not os.path.exists(changes_folder):
            os.makedirs(changes_folder, exist_ok=True)
        
        output_path = generate_instruction_file(
            self.project_path,
            selected_paths,
            prompt,
            self.current_mode
        )
        
        self.show_success(f"Instrucciones generadas:\n{output_path}")
    
    def apply_changes(self):
        if not self.changes_path or not self.project_path:
            self.show_error("Selecciona las carpetas de proyecto y cambios")
            return
        
        from core.change_parser import parse_changes
        from ui.change_reviewer import ChangeReviewerWindow
        
        print(f"DEBUG - project_path: {self.project_path}")
        print(f"DEBUG - changes_path: {self.changes_path}")
        
        changes, errors = parse_changes(self.changes_path, self.project_path)
        
        print(f"DEBUG - cambios encontrados: {len(changes)}")
        print(f"DEBUG - errores: {len(errors)}")
        for e in errors:
            print(f"DEBUG error: {e}")
        
        if not changes:
            self.show_error(f"No se encontraron cambios para procesar\nErrors: {errors}")
            return
        
        reviewer = ChangeReviewerWindow(self, self.project_path, changes)
        reviewer.lift()
        reviewer.focus_force()
    
    def show_error(self, message):
        error_win = ctk.CTkToplevel(self)
        error_win.transient(self)
        error_win.attributes("-topmost", True)
        error_win.title("Error")
        error_win.geometry("400x150")
        
        ctk.CTkLabel(
            error_win,
            text=f"❌ {message}",
            font=ctk.CTkFont(size=14)
        ).pack(expand=True)
        
        ctk.CTkButton(error_win, text="Aceptar", command=error_win.destroy).pack(pady=10)
    
    def show_success(self, message):
        success_win = ctk.CTkToplevel(self)
        success_win.transient(self)
        success_win.attributes("-topmost", True)
        success_win.title("Éxito")
        success_win.geometry("500x200")
        
        ctk.CTkLabel(
            success_win,
            text=f"✅ {message}",
            font=ctk.CTkFont(size=14),
            wraplength=450
        ).pack(expand=True)
        
        ctk.CTkButton(success_win, text="Aceptar", command=success_win.destroy).pack(pady=10)


if __name__ == "__main__":
    app = AICodeEditor()
    app.protocol("WM_DELETE_WINDOW", lambda: (app.detener_watcher() if hasattr(app, 'watcher') and app.watcher else None, app.destroy()))
    app.mainloop()
