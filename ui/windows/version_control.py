import customtkinter as ctk
import os
import difflib
import threading
from tkinter import Text
from tkinter import ttk

from services.file_watcher import ProjectWatcher
from ui.windows.version_control_controller import (
    get_git_status, get_last_commit_info, get_files_with_changes,
    get_file_status, do_commit, do_revert_file, do_discard_all_changes,
    get_file_diff_data, has_changes_to_commit
)


class VersionControlWindow(ctk.CTkToplevel):
    def __init__(self, parent, project_path: str):
        super().__init__()
        
        self.title("Control de Versiones")
        self.geometry("1000x700")
        
        self.transient(parent)
        self.project_path = project_path
        self.watcher = getattr(parent, 'watcher', None)
        
        self.selected_file = None
        self.file_versions = []
        
        self.setup_ui()
        self.load_data()
    
    def setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        header = ctk.CTkFrame(self)
        header.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        
        ctk.CTkLabel(
            header,
            text="📊 Control de Versiones",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(side="left", padx=10)
        
        # El botón de commit se movió a la sección de "Último Commit"
        
        # Panel Divisor (PanedWindow) para permitir redimensionar
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Separator.TPanedwindow", background="#2B2B2B", sashthickness=8, sashpad=0, borderwidth=0)
        
        paned = ttk.PanedWindow(self, orient="horizontal", style="Separator.TPanedwindow")
        paned.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        
        # Panel Izquierdo
        left_panel = ctk.CTkFrame(paned, corner_radius=0)
        paned.add(left_panel, weight=1)
        
        left_panel.grid_rowconfigure(3, weight=1)
        left_panel.grid_columnconfigure(0, weight=1)
        
        commit_section = ctk.CTkFrame(left_panel)
        commit_section.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="ew")
        commit_section.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(
            commit_section,
            text="📜 ÚLTIMO COMMIT",
            font=ctk.CTkFont(size=12, weight="bold")
        ).grid(row=0, column=0, sticky="w", pady=(0, 5))
        
        self.commit_info_frame = ctk.CTkFrame(
            commit_section, 
            fg_color="transparent", 
            border_width=1, 
            border_color="gray30"
        )
        self.commit_info_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        self.commit_info_frame.grid_columnconfigure(0, weight=1)
        
        self.lbl_commit_msg = ctk.CTkLabel(
            self.commit_info_frame, 
            text="-", 
            font=ctk.CTkFont(size=13, weight="bold"), 
            wraplength=250, 
            justify="left", 
            anchor="w"
        )
        self.lbl_commit_msg.grid(row=0, column=0, sticky="w", padx=10, pady=(5, 0))
        
        self.lbl_commit_hash = ctk.CTkLabel(
            self.commit_info_frame,
            text="",
            font=ctk.CTkFont(family="Consolas", size=11),
            text_color="#8e44ad"
        )
        self.lbl_commit_hash.grid(row=0, column=1, sticky="ne", padx=10, pady=(7, 0))
        
        self.lbl_commit_meta = ctk.CTkLabel(
            self.commit_info_frame, 
            text="-", 
            font=ctk.CTkFont(size=11), 
            text_color="gray", 
            anchor="w",
            justify="left"
        )
        self.lbl_commit_meta.grid(row=1, column=0, columnspan=2, sticky="w", padx=10, pady=(0, 5))
        
        # Contenedor para los botones de acción del commit
        action_frame = ctk.CTkFrame(commit_section, fg_color="transparent")
        action_frame.grid(row=2, column=0, pady=(5, 10))
        
        ctk.CTkButton(
            action_frame,
            text="↩️ Descartar",
            command=self.revert_last_commit,
            fg_color="#d63031",
            hover_color="#b71c1c",
            height=30
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            action_frame,
            text="📤 Hacer Commit",
            command=self.show_commit_dialog,
            fg_color="#6f42c1",
            height=30
        ).pack(side="left", padx=5)
        
        files_section = ctk.CTkFrame(left_panel)
        files_section.grid(row=2, column=0, padx=5, pady=(10, 5), sticky="ew")
        files_section.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(
            files_section,
            text="📄 ARCHIVOS CON CAMBIOS",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, sticky="w", pady=(0, 5))
        
        self.files_list = ctk.CTkScrollableFrame(left_panel, width=300, height=400)
        self.files_list.grid(row=3, column=0, sticky="nsew", padx=5, pady=5)
        
        self.status_label = ctk.CTkLabel(
            left_panel,
            text="",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        self.status_label.grid(row=4, column=0, padx=10, pady=10, sticky="w")
        
        # Panel Derecho
        right_panel = ctk.CTkFrame(paned, corner_radius=0)
        paned.add(right_panel, weight=3)
        
        right_panel.grid_rowconfigure(1, weight=1)
        
        diff_header_frame = ctk.CTkFrame(right_panel, fg_color="transparent")
        diff_header_frame.pack(fill="x", padx=10, pady=(10, 5))
        
        self.diff_header_label = ctk.CTkLabel(
            diff_header_frame,
            text="📄 Selecciona un archivo",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.diff_header_label.pack(side="left")
        
        diff_container = ctk.CTkFrame(right_panel)
        diff_container.pack(fill="both", expand=True, padx=10, pady=5)
        
        diff_container.grid_columnconfigure(0, weight=1)
        diff_container.grid_columnconfigure(1, weight=1)
        diff_container.grid_columnconfigure(2, weight=0) # Columna para el scrollbar
        diff_container.grid_rowconfigure(1, weight=1)
        
        ctk.CTkLabel(
            diff_container,
            text="Original (Último Commit)",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#51cf66"
        ).grid(row=0, column=0, pady=(0, 5))
        
        ctk.CTkLabel(
            diff_container,
            text="Nuevo (Aplicado)",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#ff6b6b"
        ).grid(row=0, column=1, pady=(0, 5))
        
        # Scrollbar compartido
        self.diff_scrollbar = ctk.CTkScrollbar(
            diff_container,
            command=self.sync_scroll_command
        )
        self.diff_scrollbar.grid(row=1, column=2, sticky="ns")

        self.original_text = Text(
            diff_container,
            font=("Consolas", 10),
            bg="#1E1E1E",
            fg="white",
            wrap="none",
            yscrollcommand=self.diff_scrollbar.set,
            borderwidth=0,
            highlightthickness=0
        )
        self.original_text.grid(row=1, column=0, sticky="nsew", padx=(0, 1))
        
        self.new_text = Text(
            diff_container,
            font=("Consolas", 10),
            bg="#1E1E1E",
            fg="white",
            wrap="none",
            yscrollcommand=self.diff_scrollbar.set,
            borderwidth=0,
            highlightthickness=0
        )
        self.new_text.grid(row=1, column=1, sticky="nsew", padx=(1, 0))
        
        # Config tags
        for t in [self.original_text, self.new_text]:
            t.tag_config("eliminado", background="#3A1E1E")
            t.tag_config("agregado", background="#1E3A1E")
            t.tag_config("normal", background="#1E1E1E")
        
        # Bindings para sincronizar scroll con rueda del ratón
        self.original_text.bind("<MouseWheel>", self.sync_mouse_wheel)
        self.new_text.bind("<MouseWheel>", self.sync_mouse_wheel)
        # Para Linux (eventos Button-4 y Button-5)
        self.original_text.bind("<Button-4>", self.sync_mouse_wheel)
        self.original_text.bind("<Button-5>", self.sync_mouse_wheel)
        self.new_text.bind("<Button-4>", self.sync_mouse_wheel)
        self.new_text.bind("<Button-5>", self.sync_mouse_wheel)

    def sync_scroll_command(self, *args):
        """Sincroniza el movimiento de la barra de scroll hacia ambos textos"""
        self.original_text.yview(*args)
        self.new_text.yview(*args)
        
    def sync_mouse_wheel(self, event):
        """Sincroniza el evento de la rueda del ratón"""
        # Windows/MacOS
        if event.delta:
            # Dividir por 120 es estándar para Windows, negativo para subir/bajar natural
            units = int(-1*(event.delta/120))
            self.original_text.yview_scroll(units, "units")
            self.new_text.yview_scroll(units, "units")
        # Linux (Button-4 sube, Button-5 baja)
        elif event.num == 4:
            self.original_text.yview_scroll(-1, "units")
            self.new_text.yview_scroll(-1, "units")
        elif event.num == 5:
            self.original_text.yview_scroll(1, "units")
            self.new_text.yview_scroll(1, "units")
        
        # Retornar "break" evita que el evento se propague y cause doble scroll
        return "break"
    
    def load_data(self):
        # 1. UI Loading State
        self.status_label.configure(text="Cargando cambios...")
        self.lbl_commit_msg.configure(text="Cargando...")
        self.lbl_commit_hash.configure(text="")
        self.lbl_commit_meta.configure(text="")
        
        for widget in self.files_list.winfo_children():
            widget.destroy()
            
        loading_lbl = ctk.CTkLabel(self.files_list, text="⏳ Analizando repositorio...", text_color="gray")
        loading_lbl.pack(pady=20)
        
        # 2. Iniciar carga en hilo secundario
        threading.Thread(target=self._load_data_thread, daemon=True).start()

    def _load_data_thread(self):
        commit = get_last_commit_info(self.project_path)
        all_files = get_files_with_changes(self.project_path)
        files_data = []
        for f in all_files:
            status = get_file_status(self.project_path, f)
            files_data.append((f, status))
            
        self.after(0, lambda: self._update_ui_with_data(commit, files_data))

    def _update_ui_with_data(self, commit, files_data):
        if commit:
            self.lbl_commit_msg.configure(text=commit['message'])
            self.lbl_commit_hash.configure(text=f"#{commit['short_hash']}")
            self.lbl_commit_meta.configure(text=f"👤 {commit['author']} on {commit['author_date']}")
        else:
            self.lbl_commit_msg.configure(text="No hay historial de versiones aún.")
            self.lbl_commit_hash.configure(text="")
            self.lbl_commit_meta.configure(text="")
        
        for widget in self.files_list.winfo_children():
            widget.destroy()
        
        if not files_data:
            ctk.CTkLabel(
                self.files_list,
                text="No hay archivos con cambios",
                text_color="gray"
            ).pack(pady=20)
            self.status_label.configure(text="")
            return
        
        total = len(files_data)
        self.status_label.configure(text=f"Estado: {total} cambio(s) sin commit")
        
        for filename, file_status in files_data:
            self.create_file_card(filename, file_status)
    
    def create_file_card(self, filename: str, file_status: dict):
        version_count = file_status['version_count']
        
        card = ctk.CTkFrame(self.files_list, width=500)
        card.pack(fill="x", pady=3, padx=2)
        card.grid_columnconfigure(0, weight=1)
        card.grid_columnconfigure(1, weight=0)
        
        ctk.CTkLabel(
            card,
            text=os.path.basename(filename),
            font=ctk.CTkFont(size=12),
            anchor="w",
            justify="left",
            wraplength=150
        ).grid(row=0, column=0, padx=10, sticky="ew")
        
        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.grid(row=0, column=1, padx=5, sticky="e")
        
        ctk.CTkButton(
            btn_frame,
            text="📄 Ver",
            command=lambda: self.show_file_diff(filename),
            width=70,
            height=28
        ).pack(side="left", padx=2)
        
        ctk.CTkButton(
            btn_frame,
            text="↩️",
            command=lambda: self.revert_to_commit(filename),
            fg_color="#d63031",
            width=40,
            height=28
        ).pack(side="left", padx=2)
    
    def show_file_diff(self, filename: str):
        self.selected_file = filename
        
        # Siempre usar 0 para comparar HEAD con el archivo actual en disco
        diff_data = get_file_diff_data(self.project_path, filename, 0)
        
        self.diff_header_label.configure(text=f"📄 {os.path.basename(filename)}")
        
        self.original_text.configure(state="normal")
        self.new_text.configure(state="normal")
        
        self.original_text.delete("1.0", "end")
        self.new_text.delete("1.0", "end")
        
        original_lines = diff_data['original'].split('\n') if diff_data['original'] else []
        new_lines = diff_data['modified'].split('\n') if diff_data['modified'] else []
        
        differ = difflib.Differ()
        diff_result = list(differ.compare(original_lines, new_lines))
        
        orig_line_num = 1
        new_line_num = 1
        
        for line in diff_result:
            if line.startswith('  '):
                content = line[2:]
                self.original_text.insert("end", f"{orig_line_num:4d} │ {content}\n", "normal")
                self.new_text.insert("end", f"{new_line_num:4d} │ {content}\n", "normal")
                orig_line_num += 1
                new_line_num += 1
            elif line.startswith('- '):
                content = line[2:]
                self.original_text.insert("end", f"{orig_line_num:4d} │ {content}\n", "eliminado")
                orig_line_num += 1
                self.new_text.insert("end", f"     │ \n", "normal")
            elif line.startswith('+ '):
                content = line[2:]
                self.original_text.insert("end", f"     │ \n", "normal")
                self.new_text.insert("end", f"{new_line_num:4d} │ {content}\n", "agregado")
                new_line_num += 1
        
        self.original_text.configure(state="disabled")
        self.new_text.configure(state="disabled")
    
    def revert_to_commit(self, filename: str):
        commit = get_last_commit_info(self.project_path)
        
        if not commit:
            self.show_error("No hay commits para revertir")
            return
        
        confirm = ctk.CTkToplevel(self)
        confirm.transient(self)
        confirm.attributes("-topmost", True)
        confirm.title("Confirmar Restauración")
        confirm.geometry("400x180")
        
        ctk.CTkLabel(
            confirm,
            text=f"¿Revertir {filename} al último commit?\n\n🔹 {commit['short_hash']}\n{commit['message']}\n\n⚠️ Esto sobrescribirá los cambios actuales",
            font=ctk.CTkFont(size=12),
            wraplength=350
        ).pack(pady=20)
        
        btn_frame = ctk.CTkFrame(confirm, fg_color="transparent")
        btn_frame.pack(pady=10)
        
        def do_revert():
            watcher_holder = {'watcher': self.watcher} if self.watcher else {}
            if self.watcher:
                self.watcher.ignorar = True
            success, result = do_revert_file(self.project_path, filename, commit['hash'], watcher_holder)
            if self.watcher:
                self.watcher.ignorar = False
            
            if success:
                confirm.destroy()
                self.load_data()
                self.original_text.delete("1.0", "end")
                self.original_text.insert("1.0", "(Archivo revertido)")
                self.original_text.configure(state="disabled")
                self.new_text.delete("1.0", "end")
                self.new_text.insert("1.0", "(Archivo revertido)")
                self.new_text.configure(state="disabled")
                self.show_success(result)
            else:
                self.show_error(f"Error al revertir:\n{result}")
        
        ctk.CTkButton(
            btn_frame,
            text="✅ Sí, Revertir",
            command=do_revert,
            fg_color="red",
            width=120
        ).pack(side="left", padx=10)
        
        ctk.CTkButton(
            btn_frame,
            text="❌ Cancelar",
            command=confirm.destroy,
            width=100
        ).pack(side="left", padx=10)
    
    def show_commit_dialog(self):
        if not has_changes_to_commit(self.project_path):
            self.show_error("No hay cambios para hacer commit")
            return
        
        dialog = ctk.CTkToplevel(self)
        dialog.transient(self)
        dialog.attributes("-topmost", True)
        dialog.title("Hacer Commit")
        dialog.geometry("500x250")
        
        ctk.CTkLabel(
            dialog,
            text="📤 Mensaje de Commit:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=(20, 10))
        
        from services.git_service import get_default_commit_message
        commit_msg = ctk.CTkTextbox(dialog, height=80)
        commit_msg.pack(pady=10, padx=20, fill="x")
        commit_msg.insert("1.0", get_default_commit_message())
        
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(pady=20)
        
        def do_commit_action():
            msg = commit_msg.get("1.0", "end-1c").strip()
            if not msg:
                self.show_error("El mensaje no puede estar vacío")
                return
            
            success, result = do_commit(self.project_path, msg)
            
            if success:
                dialog.destroy()
                self.load_data()
                self.show_success(result)
            else:
                self.show_error(result)
        
        ctk.CTkButton(
            btn_frame,
            text="✅ Confirmar Commit",
            command=do_commit_action,
            fg_color="green",
            width=150
        ).pack(side="left", padx=10)
        
        ctk.CTkButton(
            btn_frame,
            text="❌ Cancelar",
            command=dialog.destroy,
            width=100
        ).pack(side="left", padx=10)
    
    def revert_last_commit(self):
        commit = get_last_commit_info(self.project_path)
        
        if not commit:
            self.show_error("No hay commits para revertir")
            return
        
        confirm = ctk.CTkToplevel(self)
        confirm.transient(self)
        confirm.attributes("-topmost", True)
        confirm.title("Descartar Cambios")
        confirm.geometry("450x180")
        
        ctk.CTkLabel(
            confirm,
            text=f"¿Descartar todos los cambios locales?\n\n🔹 Último commit: {commit['short_hash']}\n{commit['message']}\n\n⚠️ Se perderán todos los cambios sin commit",
            font=ctk.CTkFont(size=12),
            wraplength=400
        ).pack(pady=20)
        
        btn_frame = ctk.CTkFrame(confirm, fg_color="transparent")
        btn_frame.pack(pady=10)
        
        def do_revert():
            watcher_holder = {'watcher': self.watcher} if self.watcher else {}
            if self.watcher:
                self.watcher.ignorar = True
            success, msg = do_discard_all_changes(self.project_path, watcher_holder)
            if self.watcher:
                self.watcher.ignorar = False
            
            if success:
                confirm.destroy()
                self.load_data()
                self.show_success("Todos los cambios locales han sido descartados")
            else:
                self.show_error(f"Error al descartar cambios:\n{msg}")
        
        ctk.CTkButton(
            btn_frame,
            text="✅ Sí, Descartar Todo",
            command=do_revert,
            fg_color="red",
            width=140
        ).pack(side="left", padx=10)
        
        ctk.CTkButton(
            btn_frame,
            text="❌ Cancelar",
            command=confirm.destroy,
            width=100
        ).pack(side="left", padx=10)
    
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
        success_win.geometry("300x100")
        
        ctk.CTkLabel(
            success_win,
            text=f"✅ {message}",
            font=ctk.CTkFont(size=14)
        ).pack(expand=True)
        
        ctk.CTkButton(success_win, text="Aceptar", command=success_win.destroy).pack(pady=10)
