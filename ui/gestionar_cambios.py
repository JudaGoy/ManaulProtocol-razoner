import customtkinter as ctk
import os
import difflib
from tkinter import scrolledtext
from tkinter import ttk
from typing import List, Dict, Optional

from core.change_parser import Change, ChangeError, apply_change, get_file_diff, parse_xml_content, normalize_text
from utils.git_manager import get_status, get_history, commit, restore, get_commit_diff, get_default_commit_message, get_commit_count, get_file_at_commit, get_current_file_content, revert_file, get_modified_files_since_commit, get_commit_files, get_uncommitted_files, discard_all_changes
from utils.apply_history import apply_change_with_history, get_files_with_history, clear_apply_history, clear_all_apply_history, get_history_snapshots
from utils.file_watcher import ProjectWatcher


class GestionarCambiosWindow(ctk.CTkToplevel):
    """
    Ventana principal para gestionar los cambios detectados en el archivo _changes.txt.
    Permite visualizar, aceptar, rechazar y modificar los cambios propuestos por la IA.
    """
    def __init__(self, parent, project_path: str, changes_file: str):
        """Inicializa la ventana de gestión de cambios."""
        super().__init__(parent)
        
        self.title("Gestionar Cambios")
        self.geometry("1000x700")
        
        self.transient(parent)
        
        self.main_window = parent
        self.project_path = project_path
        self.changes_file = changes_file
        self.change_widgets = {}
        self.changes = []
        
        # Observador para detectar cambios externos en _changes.txt
        self.watcher = ProjectWatcher(project_path, self.on_external_change)
        self.watcher.iniciar()
        
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        
        self.setup_ui()
        self.load_changes()
    
    # --- Gestión de Ventana y Eventos Externos ---

    def on_close(self):
        """Maneja el cierre de la ventana, deteniendo el watcher."""
        if hasattr(self, 'watcher'):
            self.watcher.detener()
        self.destroy()
    
    def on_external_change(self):
        """Recarga los datos si el archivo _changes.txt cambia externamente."""
        self.load_data()
    
    # --- Configuración de la Interfaz de Usuario (UI) ---

    def setup_ui(self):
        """Configura y construye todos los elementos gráficos de la ventana."""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # 1. Cabecera con botones globales
        header = ctk.CTkFrame(self)
        header.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        
        self.header_label = ctk.CTkLabel(
            header,
            text="📋 Cambios detectados: 0",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        self.header_label.pack(side="left", padx=10)
        
        btn_frame = ctk.CTkFrame(header)
        btn_frame.pack(side="right", padx=10)
        
        ctk.CTkButton(
            btn_frame,
            text="✅ Aceptar Todos",
            command=self.accept_all,
            fg_color="green"
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            btn_frame,
            text="❌ Rechazar Todos",
            command=self.reject_all,
            fg_color="red"
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            btn_frame,
            text="📊 Control de Versiones",
            command=self.show_version_control,
            fg_color="#fd7e14",
            width=160
        ).pack(side="left", padx=5)
        
        # Configuración de estilos para el PanedWindow (divisor redimensionable)
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(
            "TPanedwindow", 
            background="#2B2B2B",
            sashthickness=2,
            sashpad=1,
            borderwidth=0
        )
        
        paned = ttk.PanedWindow(self, orient="vertical", style="TPanedwindow")
        paned.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        
        # 2. Panel Superior: Lista de tarjetas de cambios
        top_frame = ctk.CTkFrame(paned, corner_radius=0)
        paned.add(top_frame, weight=1)
        
        self.changes_container = ctk.CTkScrollableFrame(top_frame)
        self.changes_container.pack(fill="both", expand=True, padx=5, pady=(5, 0))
        
        # 3. Panel Inferior: Editor de texto raw (_changes.txt)
        bottom_frame = ctk.CTkFrame(paned, corner_radius=0)
        paned.add(bottom_frame, weight=1)
        
        text_container = ctk.CTkFrame(bottom_frame)
        text_container.pack(fill="both", expand=True, padx=5, pady=(0, 5))
        
        ctk.CTkLabel(
            text_container,
            text="📝 Contenido de _changes.txt:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=5, pady=(5,0))
        
        text_area_frame = ctk.CTkFrame(text_container, fg_color="transparent")
        text_area_frame.pack(fill="both", expand=True, pady=5)
        
        self.text_content = ctk.CTkTextbox(
            text_area_frame,
            font=("Consolas", 11),
            text_color="white",
            fg_color="#1E1E1E",
            wrap="none",
            undo=True
        )
        self.text_content.pack(side="left", fill="both", expand=True)
        
        self.load_text_content()
        
        # 4. Barra de Estado y Botones del Editor
        self.status_frame = ctk.CTkFrame(self)
        self.status_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=10)
        
        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="Carga cambios desde el panel de arriba o pega nuevo contenido abajo",
            font=ctk.CTkFont(size=12)
        )
        self.status_label.pack(side="left", padx=10, pady=5)

        ctk.CTkButton(
            self.status_frame,
            text="💾 Guardar",
            command=self.save_content,
            fg_color="green",
            width=120
        ).pack(side="right", padx=10, pady=5)

        ctk.CTkButton(
            self.status_frame,
            text="▼",
            command=self.scroll_to_bottom,
            width=40,
            height=30,
            font=ctk.CTkFont(size=14)
        ).pack(side="right", padx=2, pady=5)

        ctk.CTkButton(
            self.status_frame,
            text="▲",
            command=self.scroll_to_top,
            width=40,
            height=30,
            font=ctk.CTkFont(size=14)
        ).pack(side="right", padx=2, pady=5)
    
    # --- Manejo del Editor de Texto (_changes.txt) ---

    def load_text_content(self):
        """Carga el contenido crudo del archivo de cambios en el editor inferior."""
        try:
            with open(self.changes_file, 'r', encoding='utf-8') as f:
                content = f.read()
            content = normalize_text(content)
            self.text_content.delete("1.0", "end")
            self.text_content.insert("1.0", content)
            self.scroll_to_bottom()
        except Exception as e:
            self.text_content.insert("1.0", f"Error al cargar: {str(e)}")
    
    def scroll_to_top(self):
        """Desplaza la vista del editor de texto hacia el principio."""
        self.text_content.see("1.0")
    
    def scroll_to_bottom(self):
        """Desplaza la vista del editor de texto hacia el final."""
        self.text_content.see("end")
    
    def save_content(self):
        """Guarda los cambios manuales hechos en el editor de texto."""
        try:
            content = self.text_content.get("1.0", "end-1c")
            content = normalize_text(content)
            with open(self.changes_file, 'w', encoding='utf-8') as f:
                f.write(content)
            self.load_changes()
            self.status_label.configure(text="✅ Contenido guardado correctamente")
        except Exception as e:
            self.show_error(f"Error al guardar: {str(e)}")
    
    # --- Carga y Visualización de Cambios (Tarjetas) ---

    def load_changes(self):
        """Parsea el archivo XML y genera las tarjetas visuales para cada cambio."""
        self.changes = []
        self.change_widgets = {}
        
        for widget in self.changes_container.winfo_children():
            widget.destroy()
        
        try:
            with open(self.changes_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if content.strip():
                self.changes, errors = parse_xml_content(content, self.project_path)
                
                if errors:
                    self.status_label.configure(text=f"⚠️ Errores: {len(errors)}")
        except Exception:
            pass
        
        for i, change in enumerate(self.changes):
            card = self.create_change_card(change, i)
            card.pack(fill="x", pady=5, padx=5)
        
        self.update_count_label()
    
    def create_change_card(self, change: Change, index: int):
        """Crea un widget visual para un cambio individual."""
        card = ctk.CTkFrame(self.changes_container)
        
        rel_path = os.path.relpath(change.file_path, self.project_path)
        
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(
            header,
            text=f"📄 {rel_path}",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(side="left")
        
        action_text = {
            'reemplazar': '🔄 Reemplazar',
            'insertar': '➕ Insertar',
            'eliminar': '🗑️ Eliminar',
            'crear': '✨ Crear archivo',
            'crear_carpeta': '📁 Crear carpeta',
            'eliminar_archivo': '🗑️ Eliminar archivo',
            'eliminar_carpeta': '🗑️ Eliminar carpeta',
            'patch': '🔧 Parche Git',
            'parche': '🔧 Parche Git'
        }.get(change.action, change.action)
        
        instances_text = ""
        if hasattr(change, 'instances') and change.instances != "all":
            instances_text = f" | Instancias: {change.instances}"
        
        ctk.CTkLabel(
            header,
            text=f"{action_text}{instances_text}",
            font=ctk.CTkFont(size=12)
        ).pack(side="right")
        
        diff_frame = ctk.CTkFrame(card)
        diff_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Obtener y mostrar el diff
        old_lines, new_lines = get_file_diff(change)
        
        diff_text = scrolledtext.ScrolledText(
            diff_frame,
            height=8,
            font=("Consolas", 10),
            bg="#1E1E1E",
            fg="white"
        )
        diff_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        diff_content = ""
        
        # Lógica de visualización específica para parches
        if change.action in ['patch', 'parche']:
             # Mostramos el diff crudo tal cual viene, ya tiene formato diff
             diff_content = change.new_code
        elif change.action in ['crear_carpeta', 'eliminar_carpeta']:
            if new_lines:
                for line in new_lines:
                    diff_content += f"{line}\n"
        else:
            if old_lines:
                diff_content += "--- Código original (-):\n"
                for line in old_lines:
                    diff_content += f"- {line.rstrip()}\n"
            
            if new_lines:
                diff_content += "\n+++ Código nuevo (+):\n"
                for line in new_lines:
                    diff_content += f"+ {line.rstrip()}\n"
        
        diff_text.insert("1.0", diff_content)
        diff_text.configure(state="disabled")
        
        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=5)
        
        self.change_widgets[index] = {
            'change': change,
            'card': card,
            'accepted': False
        }
        
        accept_btn = ctk.CTkButton(
            btn_frame,
            text="✅ Aceptar",
            command=lambda idx=index: self.accept_change(idx),
            fg_color="green",
            width=120
        )
        accept_btn.pack(side="left", padx=5)
        
        reject_btn = ctk.CTkButton(
            btn_frame,
            text="❌ Rechazar",
            command=lambda idx=index: self.reject_change(idx),
            fg_color="red",
            width=120
        )
        reject_btn.pack(side="left", padx=5)
        
        return card
    
    # --- Acciones de Aceptación/Rechazo de Cambios ---

    def accept_change(self, index):
        """Aplica un cambio específico al código base."""
        widget_data = self.change_widgets.get(index)
        
        if not widget_data:
            return
        
        if not widget_data['accepted']:
            change = widget_data['change']
            
            self.watcher.ignorar = True
            
            rel_path = os.path.relpath(change.file_path, self.project_path)
            
            # Cambios estructurales (archivos/carpetas)
            if change.action in ['crear_carpeta', 'crear', 'eliminar_archivo', 'eliminar_carpeta']:
                original_code = get_file_at_commit(self.project_path, "HEAD", rel_path)
                if not original_code:
                    original_code = ""
                
                success = apply_change(change, self.project_path)
                
                self.watcher.ignorar = False
                
                if success:
                    if change.action == 'crear':
                        save_change(self.project_path, rel_path, "", change.new_code)
                    elif change.action == 'eliminar':
                        save_change(self.project_path, rel_path, original_code, "")
                    
                    if change.action in ['crear', 'crear_carpeta']:
                        if hasattr(self.main_window, 'refresh_tree'):
                            self.main_window.refresh_tree(select_new=True)
                    
                    widget_data['accepted'] = True
                    widget_data['card'].configure(fg_color="#1a3d1a")
                    self.remove_applied_block(index)
                    self.hide_applied_change(index)
                    self.update_status()
                else:
                    self.show_error(f"No se pudo aplicar el cambio #{index + 1}\n\nLa IA puede haber generado código incorrecto o el archivo cambió.")
            # Cambios de contenido (edición de código)
            else:
                original_code = get_file_at_commit(self.project_path, "HEAD", rel_path)
                if original_code is None: # Si el archivo es nuevo en este commit
                    original_code = ""

                success, error_msg = apply_change_with_history(self.project_path, change, original_code)
                
                self.watcher.ignorar = False
                
                if success:
                    widget_data['accepted'] = True
                    widget_data['card'].configure(fg_color="#1a3d1a")
                    self.remove_applied_block(index)
                    self.hide_applied_change(index)
                    self.update_status()
                else:
                    self.show_error(f"No se pudo aplicar el cambio #{index + 1}\n\n{error_msg}\n\nLa IA puede haber generado código incorrecto o el archivo cambió.")
    
    def reject_change(self, index):
        """Rechaza un cambio (solo visualmente lo marca como rechazado)."""
        widget_data = self.change_widgets.get(index)
        
        if not widget_data:
            return
        
        widget_data['card'].configure(fg_color="#3d1a1a")
        self.hide_applied_change(index)
        self.update_status()
    
    def remove_applied_block(self, index):
        """Elimina el bloque XML correspondiente del editor de texto inferior tras aplicar el cambio."""
        widget_data = self.change_widgets.get(index)
        
        if not widget_data:
            return
        
        change = widget_data['change']
        
        content = self.text_content.get("1.0", "end-1c")
        
        # Intenta eliminar el bloque exacto, o busca por el código antiguo
        import re
        
        if hasattr(change, 'raw_xml') and change.raw_xml:
            raw = change.raw_xml.strip()
            if raw in content:
                new_content = content.replace(change.raw_xml, "", 1)
            else:
                pattern = re.escape(raw)
                new_content = re.sub(pattern, "", content, count=1)
        elif hasattr(change, 'old_code') and change.old_code:
            old = change.old_code.strip()
            pattern = re.escape(old)
            new_content = re.sub(pattern, "", content, count=1)
        else:
            return
        
        with open(self.changes_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        self.text_content.delete("1.0", "end")
        self.text_content.insert("1.0", new_content)
    
    def accept_all(self):
        """Itera sobre todos los cambios pendientes y los aplica."""
        accepted_count = 0
        indices_to_hide = []
        
        self.watcher.ignorar = True
        
        for i in list(self.change_widgets.keys()):
            widget_data = self.change_widgets.get(i)
            if widget_data and not widget_data['accepted']:
                change = widget_data['change']
                rel_path = os.path.relpath(change.file_path, self.project_path)
                
                if change.action in ['crear_carpeta', 'crear', 'eliminar_archivo', 'eliminar_carpeta']:
                    original_code = get_file_at_commit(self.project_path, "HEAD", rel_path)
                    if not original_code:
                        original_code = ""
                    
                    success = apply_change(change, self.project_path)
                    if success:
                        if change.action == 'crear':
                            save_change(self.project_path, rel_path, "", change.new_code)
                        elif change.action == 'eliminar':
                            save_change(self.project_path, rel_path, original_code, "")
                        
                        if change.action in ['crear', 'crear_carpeta']:
                            if not hasattr(self, '_tree_refreshed'):
                                self._tree_refreshed = True
                                if hasattr(self.main_window, 'refresh_tree'):
                                    self.main_window.refresh_tree(select_new=True)
                        
                        widget_data['accepted'] = True
                        widget_data['card'].configure(fg_color="#1a3d1a")
                        accepted_count += 1
                        self.remove_applied_block(i)
                        indices_to_hide.append(i)
                else:
                    original_code = get_file_at_commit(self.project_path, "HEAD", rel_path)
                    if original_code is None:
                        original_code = ""

                    success, error_msg = apply_change_with_history(self.project_path, change, original_code)

                    if success:
                        if change.action in ['crear', 'crear_carpeta']:
                            if not hasattr(self, '_tree_refreshed'):
                                self._tree_refreshed = True
                                if hasattr(self.main_window, 'refresh_tree'):
                                    self.main_window.refresh_tree(select_new=True)
                        
                        widget_data['accepted'] = True
                        widget_data['card'].configure(fg_color="#1a3d1a")
                        accepted_count += 1
                        self.remove_applied_block(i)
                        indices_to_hide.append(i)
        
        self.watcher.ignorar = False
        
        if hasattr(self.main_window, 'refresh_tree') and accepted_count > 0:
            self.main_window.refresh_tree(select_new=True)
        
        self.update_status()
        
        for i in indices_to_hide:
            self.hide_applied_change(i)
        
        self.show_info(f"Se aplicaron {accepted_count} cambios")
    
    def reject_all(self):
        """Marca todos los cambios pendientes como rechazados."""
        indices_to_hide = []
        for i in list(self.change_widgets.keys()):
            widget_data = self.change_widgets.get(i)
            if widget_data:
                widget_data['card'].configure(fg_color="#3d1a1a")
                indices_to_hide.append(i)
        
        self.update_status()
        
        for i in indices_to_hide:
            self.hide_applied_change(i)
    
    # --- Helpers de UI ---

    def hide_applied_change(self, index):
        """Oculta la tarjeta del cambio especificado de la lista visual."""
        widget_data = self.change_widgets.get(index)
        if widget_data and widget_data['card']:
            widget_data['card'].pack_forget()
            del self.change_widgets[index]
            self.update_count_label()
    
    def update_count_label(self):
        """Actualiza la etiqueta que muestra la cantidad de cambios restantes."""
        remaining = len(self.change_widgets)
        self.header_label.configure(text=f"📋 Cambios restantes: {remaining}")
    
    def update_status(self):
        """Recalcula y actualiza la barra de estado con contadores de cambios."""
        accepted = sum(1 for w in self.change_widgets.values() if w['accepted'])
        total = len(self.change_widgets)
        
        pending = total - accepted
        
        self.status_label.configure(
            text=f"✅ Aceptados: {accepted} | ⏳ Pendientes: {pending} | ❌ Rechazados: {total - accepted - pending}"
        )
    
    def show_error(self, message):
        """Muestra un cuadro de diálogo de error modal."""
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
    
    def show_info(self, message):
        """Muestra un cuadro de diálogo de información modal."""
        info_win = ctk.CTkToplevel(self)
        info_win.transient(self)
        info_win.attributes("-topmost", True)
        info_win.title("Información")
        info_win.geometry("300x100")
        
        ctk.CTkLabel(info_win, text=f"ℹ️ {message}").pack(expand=True)
        ctk.CTkButton(info_win, text="Aceptar", command=info_win.destroy).pack(pady=5)
    
    def show_version_control(self):
        """Abre la ventana de Control de Versiones."""
        VersionControlWindow(self, self.project_path)


class VersionControlWindow(ctk.CTkToplevel):
    """
    Ventana para realizar operaciones de Git (commit, revert) y visualizar el
    estado actual de los archivos comparado con el último commit.
    """
    def __init__(self, parent, project_path: str):
        """Inicializa la ventana de control de versiones."""
        super().__init__(parent)
        
        self.title("Control de Versiones")
        self.geometry("1000x700")
        
        self.transient(parent)
        self.project_path = project_path
        
        self.selected_file = None
        self.current_version_index = 0
        self.file_versions = []
        
        self.setup_ui()
        self.load_data()
    
    # --- Configuración de UI ---

    def setup_ui(self):
        """Configura los paneles y widgets de la ventana de control de versiones."""
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(1, weight=1)
        
        header = ctk.CTkFrame(self)
        header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=10)
        
        ctk.CTkLabel(
            header,
            text="📊 Control de Versiones",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(side="left", padx=10)
        
        ctk.CTkButton(
            header,
            text="📤 Hacer Commit",
            command=self.show_commit_dialog,
            fg_color="#6f42c1",
            width=120
        ).pack(side="right", padx=10)
        
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(
            "TPanedwindow",
            background="#2B2B2B",
            sashthickness=6,
            sashpad=2,
            borderwidth=0
        )
        
        paned = ttk.PanedWindow(self, orient="horizontal", style="TPanedwindow")
        paned.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        
        left_panel = ctk.CTkFrame(paned, corner_radius=0)
        paned.add(left_panel, weight=0)
        
        left_panel.grid_rowconfigure(3, weight=1)
        
        # Sección de Info del Commit
        commit_section = ctk.CTkFrame(left_panel)
        commit_section.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="ew")
        commit_section.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(
            commit_section,
            text="📜 ÚLTIMO COMMIT",
            font=ctk.CTkFont(size=12, weight="bold")
        ).grid(row=0, column=0, sticky="w", pady=(0, 5))
        
        self.commit_info_label = ctk.CTkLabel(
            commit_section,
            text="",
            font=ctk.CTkFont(size=11),
            text_color="gray",
            anchor="w",
            justify="left"
        )
        self.commit_info_label.grid(row=1, column=0, sticky="w", pady=(0, 5))
        
        self.btn_revert_commit = ctk.CTkButton(
            commit_section,
            text="↩️ Revertir Commit",
            command=self.revert_last_commit,
            fg_color="red",
            width=140,
            height=30
        )
        self.btn_revert_commit.grid(row=2, column=0, sticky="w", pady=(0, 5))
        
        # Sección de Lista de Archivos
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
        
        # Panel Derecho: Visualizador de Diff
        right_panel = ctk.CTkFrame(paned, corner_radius=0)
        paned.add(right_panel, weight=2)
        
        right_panel.grid_rowconfigure(1, weight=1)
        
        self.diff_header_label = ctk.CTkLabel(
            right_panel,
            text="📄 Diff (selecciona un archivo)",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.diff_header_label.pack(pady=(10, 5), padx=10)
        
        diff_container = ctk.CTkFrame(right_panel)
        diff_container.pack(fill="both", expand=True, padx=10, pady=5)
        
        diff_container.grid_columnconfigure(0, weight=1)
        diff_container.grid_columnconfigure(1, weight=1)
        
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
        
        self.original_text = scrolledtext.ScrolledText(
            diff_container,
            font=("Consolas", 10),
            bg="#1E1E1E",
            fg="white",
            wrap="none"
        )
        self.original_text.grid(row=1, column=0, sticky="nsew", padx=(0, 2))
        
        self.original_text.tag_config("eliminado", background="#3A1E1E")
        self.original_text.tag_config("agregado", background="#1E3A1E")
        self.original_text.tag_config("normal", background="#1E1E1E")
        
        self.new_text = scrolledtext.ScrolledText(
            diff_container,
            font=("Consolas", 10),
            bg="#1E1E1E",
            fg="white",
            wrap="none"
        )
        self.new_text.grid(row=1, column=1, sticky="nsew", padx=(2, 0))
        
        self.new_text.tag_config("eliminado", background="#3A1E1E")
        self.new_text.tag_config("agregado", background="#1E3A1E")
        self.new_text.tag_config("normal", background="#1E1E1E")
    
    # --- Carga de Datos ---

    def load_data(self):
        """Obtiene el estado actual de Git y la lista de archivos modificados."""
        history = get_history(self.project_path, limit=1)
        
        if history:
            commit = history[0]
            self.commit_info_label.configure(
                text=f"🔹 {commit['short_hash']}\n📅 {commit['author_date']}\n{commit['message']}"
            )
        else:
            self.commit_info_label.configure(
                text="No hay commits aún"
            )
        
        files_with_history = get_files_with_history(self.project_path)
        uncommitted_files = get_uncommitted_files(self.project_path)
        
        all_files = list(set(files_with_history + uncommitted_files))
        all_files.sort()
        
        for widget in self.files_list.winfo_children():
            widget.destroy()
        
        if not all_files:
            ctk.CTkLabel(
                self.files_list,
                text="No hay archivos con cambios",
                text_color="gray"
            ).pack(pady=20)
            self.status_label.configure(text="")
            return
        
        total = len(all_files)
        self.status_label.configure(text=f"Estado: {total} cambio(s) sin commit")
        
        for filename in all_files:
            self.create_file_card(filename)
    
    def create_file_card(self, filename: str):
        """Crea un elemento en la lista para un archivo modificado."""
        snapshots = get_history_snapshots(self.project_path, filename)
        version_count = len(snapshots)
        
        uncommitted = get_uncommitted_files(self.project_path)
        is_uncommitted = filename in uncommitted
        
        history = get_history(self.project_path, limit=1)
        if history:
            last_commit_code = get_file_at_commit(self.project_path, "HEAD", filename)
            current_code = get_current_file_content(self.project_path, filename)
            
            has_diff_from_commit = last_commit_code != current_code
        else:
            has_diff_from_commit = True
        
        if version_count > 0:
            status_color = "orange"
        elif is_uncommitted:
            status_color = "red"
        else:
            status_color = "green"
        
        card = ctk.CTkFrame(self.files_list, width=500)
        card.pack(fill="x", pady=3, padx=2)
        card.grid_columnconfigure(0, weight=0)
        card.grid_columnconfigure(1, weight=1)
        card.grid_columnconfigure(2, weight=0)
        card.grid_columnconfigure(3, weight=0)
        
        nav_frame = ctk.CTkFrame(card, fg_color="transparent")
        nav_frame.grid(row=0, column=0, padx=(5, 10), sticky="w")
        
        btn_prev = ctk.CTkButton(
            nav_frame,
            text="◀",
            command=lambda: self.navigate_version(filename, -1),
            width=30,
            height=28
        )
        btn_prev.pack(side="left")
        
        if version_count == 0:
            btn_prev.configure(state="disabled")
        
        ctk.CTkLabel(
            card,
            text=filename,
            font=ctk.CTkFont(size=12),
            anchor="w"
        ).grid(row=0, column=1, padx=10, sticky="ew")
        
        btn_next = ctk.CTkButton(
            nav_frame,
            text="▶",
            command=lambda: self.navigate_version(filename, 1),
            width=30,
            height=28
        )
        btn_next.pack(side="left")
        
        if version_count == 0:
            btn_next.configure(state="disabled")
        
        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.grid(row=0, column=2, columnspan=2, padx=(10, 10), sticky="e")
        
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
    
    # --- Navegación y Diff ---

    def navigate_version(self, filename: str, direction: int):
        """Navega entre las versiones del historial de aplicación de cambios."""
        snapshots = get_history_snapshots(self.project_path, filename)
        
        if direction == -1:
            if snapshots:
                self.current_version_index = len(snapshots)
            else:
                self.current_version_index = 0
        else:
            self.current_version_index = 0
        
        self.show_file_diff(filename)
        self.load_data()
    
    def show_file_diff(self, filename: str):
        """Muestra el diff side-by-side entre el último commit y la versión actual/seleccionada."""
        self.selected_file = filename
        
        snapshots = get_history_snapshots(self.project_path, filename)
        version_count = len(snapshots)
        
        last_commit_code = get_file_at_commit(self.project_path, "HEAD", filename)
        current_code = get_current_file_content(self.project_path, filename)
        
        if not last_commit_code:
            last_commit_code = "(Archivo no existe en el último commit)"
        
        applied_code = current_code
        if version_count > 0 and self.current_version_index > 0:
            idx = self.current_version_index - 1
            if idx < len(snapshots):
                applied_code = snapshots[idx]
        
        if version_count > 0:
            self.diff_header_label.configure(text=f"📄 {filename} (Aplicado sin commit - {version_count})")
        else:
            last_commit_code_check = get_file_at_commit(self.project_path, "HEAD", filename)
            if last_commit_code_check and last_commit_code_check != current_code:
                self.diff_header_label.configure(text=f"📄 {filename} (Modificado sin commit)")
            elif not last_commit_code_check:
                self.diff_header_label.configure(text=f"📄 {filename} (Nuevo archivo)")
            else:
                self.diff_header_label.configure(text=f"📄 {filename} (Sincronizado)")
        
        self.original_text.configure(state="normal")
        self.new_text.configure(state="normal")
        
        self.original_text.delete("1.0", "end")
        self.new_text.delete("1.0", "end")
        
        original_lines = last_commit_code.split('\n') if last_commit_code else []
        new_lines = applied_code.split('\n') if applied_code else []
        
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
    
    # --- Acciones de Git (Revert, Commit) ---

    def revert_to_commit(self, filename: str):
        """Revierte un archivo específico al estado del último commit."""
        history = get_history(self.project_path, limit=1)
        
        if not history:
            self.show_error("No hay commits para revertir")
            return
        
        commit = history[0]
        
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
            self.watcher.ignorar = True
            success, result = revert_file(self.project_path, filename, commit['hash'])
            self.watcher.ignorar = False
            
            if success:
                clear_apply_history(self.project_path, filename)
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
        """Muestra un diálogo para crear un nuevo commit."""
        status = get_status(self.project_path)
        has_changes = status["staged"] or status["modified"] or status["untracked"]
        
        if not has_changes:
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
        
        commit_msg = ctk.CTkTextbox(dialog, height=80)
        commit_msg.pack(pady=10, padx=20, fill="x")
        commit_msg.insert("1.0", get_default_commit_message())
        
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(pady=20)
        
        def do_commit():
            msg = commit_msg.get("1.0", "end-1c").strip()
            if not msg:
                self.show_error("El mensaje no puede estar vacío")
                return
            
            success, result = commit(self.project_path, msg)
            
            if success:
                clear_all_apply_history(self.project_path)
                dialog.destroy()
                self.load_data()
                self.show_success(result)
            else:
                self.show_error(result)
        
        ctk.CTkButton(
            btn_frame,
            text="✅ Confirmar Commit",
            command=do_commit,
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
        """Descarta TODOS los cambios locales no confirmados (reset hard a HEAD)."""
        history = get_history(self.project_path, limit=1)
        
        if not history:
            self.show_error("No hay commits para revertir")
            return
        
        commit = history[0]
        
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
            self.watcher.ignorar = True
            success, msg = discard_all_changes(self.project_path)
            self.watcher.ignorar = False
            
            if success:
                git_status = get_status(self.project_path)
                untracked = git_status.get("untracked", [])
                
                for filepath in untracked:
                    full_path = os.path.join(self.project_path, filepath)
                    if os.path.isfile(full_path):
                        try:
                            os.remove(full_path)
                        except Exception:
                            pass
                
                clear_all_apply_history(self.project_path)
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
    
    # --- Helpers ---

    def show_error(self, message):
        """Muestra un mensaje de error en una ventana modal."""
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
        """Muestra un mensaje de éxito en una ventana modal."""
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
