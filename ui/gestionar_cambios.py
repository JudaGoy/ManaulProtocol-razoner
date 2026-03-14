import customtkinter as ctk
import os
from tkinter import scrolledtext
from tkinter import ttk
from typing import List

from core.change_parser import Change, ChangeError, apply_change, get_file_diff, parse_xml_content


class GestionarCambiosWindow(ctk.CTkToplevel):
    def __init__(self, parent, project_path: str, changes_file: str):
        super().__init__(parent)
        
        self.title("Gestionar Cambios")
        self.geometry("1000x700")
        
        self.project_path = project_path
        self.changes_file = changes_file
        self.change_widgets = {}
        self.changes = []
        
        self.setup_ui()
        self.load_changes()
    
    def setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
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
        
        paned = ttk.PanedWindow(self, orient="vertical")
        paned.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        
        top_frame = ctk.CTkFrame(paned)
        paned.add(top_frame, weight=1)
        
        self.changes_container = ctk.CTkScrollableFrame(top_frame)
        self.changes_container.pack(fill="both", expand=True, padx=5, pady=5)
        
        bottom_frame = ctk.CTkFrame(paned)
        paned.add(bottom_frame, weight=1)
        
        text_container = ctk.CTkFrame(bottom_frame)
        text_container.pack(fill="both", expand=True, padx=5, pady=5)
        
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
        
        arrow_frame = ctk.CTkFrame(text_area_frame, width=40)
        arrow_frame.pack(side="right", padx=(5,10), fill="y")
        
        ctk.CTkButton(
            arrow_frame,
            text="▲",
            command=self.scroll_to_top,
            width=30,
            height=25,
            font=ctk.CTkFont(size=14)
        ).pack(pady=(0,2))
        
        ctk.CTkButton(
            arrow_frame,
            text="▼",
            command=self.scroll_to_bottom,
            width=30,
            height=25,
            font=ctk.CTkFont(size=14)
        ).pack(pady=(2,0))
        
        btn_frame = ctk.CTkFrame(bottom_frame)
        btn_frame.pack(fill="x", padx=5, pady=5)
        
        ctk.CTkButton(
            btn_frame,
            text="💾 Guardar",
            command=self.save_content,
            fg_color="green",
            width=120
        ).pack(side="right", padx=5)
        
        self.load_text_content()
        
        self.status_frame = ctk.CTkFrame(self)
        self.status_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=10)
        
        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="Carga cambios desde el panel de arriba o pega nuevo contenido abajo",
            font=ctk.CTkFont(size=12)
        )
        self.status_label.pack(pady=5)
    
    def load_text_content(self):
        try:
            with open(self.changes_file, 'r', encoding='utf-8') as f:
                content = f.read()
            self.text_content.delete("1.0", "end")
            self.text_content.insert("1.0", content)
            self.scroll_to_bottom()
        except Exception as e:
            self.text_content.insert("1.0", f"Error al cargar: {str(e)}")
    
    def scroll_to_top(self):
        self.text_content.see("1.0")
    
    def scroll_to_bottom(self):
        self.text_content.see("end")
    
    def save_content(self):
        try:
            content = self.text_content.get("1.0", "end-1c")
            with open(self.changes_file, 'w', encoding='utf-8') as f:
                f.write(content)
            self.load_changes()
            self.status_label.configure(text="✅ Contenido guardado correctamente")
        except Exception as e:
            self.show_error(f"Error al guardar: {str(e)}")
    
    def load_changes(self):
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
            'eliminar_carpeta': '🗑️ Eliminar carpeta'
        }.get(change.action, change.action)
        
        ctk.CTkLabel(
            header,
            text=f"{action_text}",
            font=ctk.CTkFont(size=12)
        ).pack(side="right")
        
        diff_frame = ctk.CTkFrame(card)
        diff_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
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
        
        if change.action in ['crear_carpeta', 'eliminar_carpeta']:
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
    
    def accept_change(self, index):
        widget_data = self.change_widgets.get(index)
        
        if not widget_data:
            return
        
        if not widget_data['accepted']:
            change = widget_data['change']
            success = apply_change(change)
            
            if success:
                widget_data['accepted'] = True
                widget_data['card'].configure(fg_color="#1a3d1a")
                self.remove_applied_block(index)
                self.hide_applied_change(index)
                self.update_status()
            else:
                rel_path = os.path.relpath(change.file_path, self.project_path)
                self.show_error(f"No se pudo aplicar el cambio #{index + 1}\n\nEl código que intentas reemplazar no existe en:\n{rel_path}\n\nLa IA puede haber generado código incorrecto o el archivo cambió.")
    
    def reject_change(self, index):
        widget_data = self.change_widgets.get(index)
        
        if not widget_data:
            return
        
        widget_data['card'].configure(fg_color="#3d1a1a")
        self.hide_applied_change(index)
        self.update_status()
    
    def remove_applied_block(self, index):
        widget_data = self.change_widgets.get(index)
        
        if not widget_data:
            return
        
        change = widget_data['change']
        
        content = self.text_content.get("1.0", "end-1c")
        
        block_start = content.find('<CAMBIOS>')
        if block_start == -1:
            return
        
        block_end = content.find('</CAMBIOS>', block_start)
        if block_end == -1:
            return
        
        block_end += len('</CAMBIOS>')
        
        full_block = content[block_start:block_end]
        
        new_content = content[:block_start] + content[block_end:]
        
        with open(self.changes_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        self.text_content.delete("1.0", "end")
        self.text_content.insert("1.0", new_content)
    
    def accept_all(self):
        accepted_count = 0
        indices_to_hide = []
        
        for i in list(self.change_widgets.keys()):
            widget_data = self.change_widgets.get(i)
            if widget_data and not widget_data['accepted']:
                success = apply_change(widget_data['change'])
                if success:
                    widget_data['accepted'] = True
                    widget_data['card'].configure(fg_color="#1a3d1a")
                    accepted_count += 1
                    self.remove_applied_block(i)
                    indices_to_hide.append(i)
        
        self.update_status()
        
        for i in indices_to_hide:
            self.hide_applied_change(i)
        
        self.show_info(f"Se aplicaron {accepted_count} cambios")
    
    def reject_all(self):
        indices_to_hide = []
        for i in list(self.change_widgets.keys()):
            widget_data = self.change_widgets.get(i)
            if widget_data:
                widget_data['card'].configure(fg_color="#3d1a1a")
                indices_to_hide.append(i)
        
        self.update_status()
        
        for i in indices_to_hide:
            self.hide_applied_change(i)
    
    def hide_applied_change(self, index):
        widget_data = self.change_widgets.get(index)
        if widget_data and widget_data['card']:
            widget_data['card'].pack_forget()
            del self.change_widgets[index]
            self.update_count_label()
    
    def update_count_label(self):
        remaining = len(self.change_widgets)
        self.header_label.configure(text=f"📋 Cambios restantes: {remaining}")
    
    def update_status(self):
        accepted = sum(1 for w in self.change_widgets.values() if w['accepted'])
        total = len(self.change_widgets)
        
        pending = total - accepted
        
        self.status_label.configure(
            text=f"✅ Aceptados: {accepted} | ⏳ Pendientes: {pending} | ❌ Rechazados: {total - accepted - pending}"
        )
    
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
    
    def show_info(self, message):
        info_win = ctk.CTkToplevel(self)
        info_win.title("Información")
        info_win.geometry("300x100")
        
        ctk.CTkLabel(info_win, text=f"ℹ️ {message}").pack(expand=True)
        ctk.CTkButton(info_win, text="Aceptar", command=info_win.destroy).pack(pady=5)
