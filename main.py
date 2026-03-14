import customtkinter as ctk
from CTkFileDialog import askdirectory
import os
import tkinter as tk
from tkinter import ttk
from tkinter import font

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
        
        self.btn_select_changes = ctk.CTkButton(
            self.sidebar,
            text="📂 Cargar Cambios",
            command=self.select_changes_folder,
            height=40,
            state="disabled"
        )
        self.btn_select_changes.pack(pady=10, padx=20, fill="x")
        
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
            text="✅ Aplicar Cambios",
            command=self.apply_changes,
            height=40,
            state="disabled"
        )
        self.btn_apply.pack(pady=10, padx=20, fill="x")
        
        separator2 = ctk.CTkFrame(self.sidebar, height=2)
        separator2.pack(pady=20, padx=20, fill="x")
        
        self.btn_check_all = ctk.CTkButton(
            self.sidebar,
            text="☑️ Seleccionar Todos",
            command=self.check_all_files,
            height=35
        )
        self.btn_check_all.pack(pady=5, padx=20, fill="x")
        
        self.btn_uncheck_all = ctk.CTkButton(
            self.sidebar,
            text="⬜ Deseleccionar Todos",
            command=self.uncheck_all_files,
            height=35
        )
        self.btn_uncheck_all.pack(pady=5, padx=20, fill="x")
        
        separator3 = ctk.CTkFrame(self.sidebar, height=2)
        separator3.pack(pady=20, padx=20, fill="x")
        
        self.btn_create_file = ctk.CTkButton(
            self.sidebar,
            text="📄 Crear Archivo",
            command=self.create_file,
            height=35
        )
        self.btn_create_file.pack(pady=5, padx=20, fill="x")
        
        self.btn_create_folder = ctk.CTkButton(
            self.sidebar,
            text="📁 Crear Carpeta",
            command=self.create_folder,
            height=35
        )
        self.btn_create_folder.pack(pady=5, padx=20, fill="x")
        
        self.btn_delete = ctk.CTkButton(
            self.sidebar,
            text="🗑️ Eliminar Seleccionado",
            command=self.delete_selected,
            height=35,
            fg_color="#8B0000",
            hover_color="#A00000"
        )
        self.btn_delete.pack(pady=5, padx=20, fill="x")
    
    def setup_main_content(self):
        self.main_content.grid_columnconfigure(0, weight=1)
        self.main_content.grid_rowconfigure(1, weight=1)
        
        self.lbl_title = ctk.CTkLabel(
            self.main_content,
            text="Selecciona un proyecto para comenzar",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        self.lbl_title.grid(row=0, column=0, pady=10, padx=10, sticky="w")
        
        self.lbl_instructions = ctk.CTkLabel(
            self.main_content,
            text="💡 Doble clic para seleccionar/deseleccionar archivos y carpetas",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        self.lbl_instructions.grid(row=0, column=0, pady=(0,5), padx=10, sticky="w")
        
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
        style.theme_use("default")
        style.configure(
            "Treeview",
            background="#2B2B2B",
            foreground="white",
            fieldbackground="#2B2B2B",
            rowheight=28,
            font=("Consolas", 11)
        )
        style.configure(
            "Treeview.Heading",
            background="#1F1F1F",
            foreground="white",
            font=("Consolas", 11, "bold")
        )
        style.map("Treeview", background=[("selected", "#3B8ED0")])
        
        self.tree_frame = ctk.CTkFrame(self.file_frame)
        self.tree_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.tree_frame.grid_columnconfigure(0, weight=1)
        self.tree_frame.grid_rowconfigure(0, weight=1)
        
        self.tree = ttk.Treeview(self.tree_frame, show="tree", selectmode="browse")
        self.tree.grid(row=0, column=0, sticky="nsew")
        
        scrollbar = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)
        self.tree.bind("<Button-1>", self.on_tree_click)
    
    def select_project(self):
        folder = askdirectory(title="Seleccionar Proyecto")
        if folder:
            self.project_path = folder
            self.lbl_project.configure(text=f"Proyecto:\n{os.path.basename(folder)}")
            self.lbl_title.configure(text=f"Archivos del proyecto: {os.path.basename(folder)}")
            self.load_project_files(folder)
            self.btn_generate.configure(state="normal")
            self.btn_select_changes.configure(state="normal")
    
    def select_changes_folder(self):
        folder = askdirectory(title="Seleccionar Carpeta de Cambios")
        if folder:
            self.changes_path = folder
            self.lbl_project.configure(
                text=f"Proyecto:\n{os.path.basename(self.project_path)}\n\nCambios:\n{os.path.basename(folder)}"
            )
            self.btn_apply.configure(state="normal")
    
    def load_project_files(self, folder):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.selected_files = {}
        self.file_tree_items = {}
        
        root_item = self.tree.insert("", "end", text=f"☑️ 📁 {os.path.basename(folder)}", open=True)
        self.file_tree_items[folder] = root_item
        
        self.add_folder_contents(folder, root_item)
        
        for item_id in self.tree.get_children(root_item):
            self.tree.item(item_id, open=True)
    
    def add_folder_contents(self, folder, parent_item):
        try:
            items = sorted(os.listdir(folder))
        except PermissionError:
            return
        
        dirs = []
        files = []
        
        for item in items:
            if item.startswith('.'):
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
                values=(path, "directory", True)
            )
            self.file_tree_items[path] = dir_item
            self.selected_files[path] = True
            self.add_folder_contents(path, dir_item)
        
        for filename in files:
            path = os.path.join(folder, filename)
            file_item = self.tree.insert(
                parent_item,
                "end",
                text=f"☑️ 📄 {filename}",
                values=(path, "file", True)
            )
            self.file_tree_items[path] = file_item
            self.selected_files[path] = True
    
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
        
        path = values[0]
        
        if path in self.selected_files:
            self.selected_files[path] = not self.selected_files[path]
            
            current_text = self.tree.item(item_id, 'text')
            
            if self.selected_files[path]:
                new_text = current_text.replace("⬜", "☑️")
                self.update_children_selection(item_id, True)
            else:
                new_text = current_text.replace("☑️", "⬜")
                self.update_children_selection(item_id, False)
            
            self.tree.item(item_id, text=new_text)
    
    def update_children_selection(self, parent_item, selected):
        children = self.tree.get_children(parent_item)
        for child in children:
            child_values = self.tree.item(child, 'values')
            if child_values:
                child_path = child_values[0]
                if child_path in self.selected_files:
                    self.selected_files[child_path] = selected
                    
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
    
    def check_all_files(self):
        for path, selected in self.selected_files.items():
            self.selected_files[path] = True
            if path in self.file_tree_items:
                item = self.file_tree_items[path]
                self.tree.item(item, text=self.tree.item(item)["text"].replace("⬜", "☑️"))
    
    def uncheck_all_files(self):
        for path, selected in self.selected_files.items():
            self.selected_files[path] = False
            if path in self.file_tree_items:
                item = self.file_tree_items[path]
                self.tree.item(item, text=self.tree.item(item)["text"].replace("☑️", "⬜"))
    
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
        
        changes, errors = parse_changes(self.changes_path, self.project_path)
        
        if not changes:
            self.show_error("No se encontraron cambios para procesar")
            return
        
        reviewer = ChangeReviewerWindow(self, self.project_path, changes)
    
    def show_error(self, message):
        error_win = ctk.CTkToplevel(self)
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
        success_win.title("Éxito")
        success_win.geometry("500x200")
        
        ctk.CTkLabel(
            success_win,
            text=f"✅ {message}",
            font=ctk.CTkFont(size=14),
            wraplength=450
        ).pack(expand=True)
        
        ctk.CTkButton(success_win, text="Aceptar", command=success_win.destroy).pack(pady=10)
    
    def create_file(self):
        if not self.project_path:
            self.show_error("Selecciona un proyecto primero")
            return
        
        dialog = ctk.CTkToplevel(self)
        dialog.title("Crear Archivo")
        dialog.geometry("400x150")
        
        ctk.CTkLabel(dialog, text="Nombre del archivo:").pack(pady=10, padx=20, anchor="w")
        
        entry = ctk.CTkEntry(dialog, width=350)
        entry.pack(pady=5, padx=20)
        
        def create():
            filename = entry.get().strip()
            if not filename:
                self.show_error("Ingresa un nombre de archivo")
                return
            
            rel_path = filename if not self.selected_files else None
            
            selected_paths = [p for p, s in self.selected_files.items() if s]
            if selected_paths:
                base_path = selected_paths[0]
                if os.path.isdir(base_path):
                    rel_path = os.path.relpath(base_path, self.project_path)
                    file_path = os.path.join(self.project_path, rel_path, filename)
                else:
                    folder = os.path.dirname(base_path)
                    rel_path = os.path.relpath(folder, self.project_path)
                    file_path = os.path.join(folder, filename)
            else:
                file_path = os.path.join(self.project_path, filename)
            
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write("")
                self.load_project_files(self.project_path)
                self.show_success(f"Archivo creado:\n{filename}")
                dialog.destroy()
            except Exception as e:
                self.show_error(f"Error al crear archivo: {str(e)}")
        
        ctk.CTkButton(dialog, text="Crear", command=create).pack(pady=15)
    
    def create_folder(self):
        if not self.project_path:
            self.show_error("Selecciona un proyecto primero")
            return
        
        dialog = ctk.CTkToplevel(self)
        dialog.title("Crear Carpeta")
        dialog.geometry("400x150")
        
        ctk.CTkLabel(dialog, text="Nombre de la carpeta:").pack(pady=10, padx=20, anchor="w")
        
        entry = ctk.CTkEntry(dialog, width=350)
        entry.pack(pady=5, padx=20)
        
        def create():
            foldername = entry.get().strip()
            if not foldername:
                self.show_error("Ingresa un nombre de carpeta")
                return
            
            selected_paths = [p for p, s in self.selected_files.items() if s]
            
            if selected_paths:
                base_path = selected_paths[0]
                if os.path.isfile(base_path):
                    folder = os.path.dirname(base_path)
                else:
                    folder = base_path
            else:
                folder = self.project_path
            
            folder_path = os.path.join(folder, foldername)
            
            try:
                os.makedirs(folder_path, exist_ok=True)
                self.load_project_files(self.project_path)
                self.show_success(f"Carpeta creada:\n{foldername}")
                dialog.destroy()
            except Exception as e:
                self.show_error(f"Error al crear carpeta: {str(e)}")
        
        ctk.CTkButton(dialog, text="Crear", command=create).pack(pady=15)
    
    def delete_selected(self):
        selected_paths = [p for p, s in self.selected_files.items() if s]
        
        if not selected_paths:
            self.show_error("No hay archivos o carpetas seleccionados")
            return
        
        confirm = ctk.CTkToplevel(self)
        confirm.title("Confirmar eliminación")
        confirm.geometry("400x200")
        
        items_count = len(selected_paths)
        
        ctk.CTkLabel(
            confirm,
            text=f"¿Eliminar {items_count} elemento(s)?",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=20)
        
        ctk.CTkLabel(
            confirm,
            text="Esta acción no se puede deshacer",
            text_color="red"
        ).pack(pady=5)
        
        btn_frame = ctk.CTkFrame(confirm, fg_color="transparent")
        btn_frame.pack(pady=20)
        
        def do_delete():
            errors = []
            for path in selected_paths:
                try:
                    if os.path.isfile(path):
                        os.remove(path)
                    elif os.path.isdir(path):
                        import shutil
                        shutil.rmtree(path)
                except Exception as e:
                    errors.append(f"{os.path.basename(path)}: {str(e)}")
            
            self.selected_files = {}
            self.file_tree_items = {}
            self.load_project_files(self.project_path)
            
            if errors:
                self.show_error("Errores:\n" + "\n".join(errors))
            else:
                self.show_success(f"Eliminados {items_count} elemento(s)")
            
            confirm.destroy()
        
        ctk.CTkButton(
            btn_frame,
            text="Eliminar",
            command=do_delete,
            fg_color="red",
            width=120
        ).pack(side="left", padx=10)
        
        ctk.CTkButton(
            btn_frame,
            text="Cancelar",
            command=confirm.destroy,
            width=120
        ).pack(side="left", padx=10)


if __name__ == "__main__":
    app = AICodeEditor()
    app.mainloop()
