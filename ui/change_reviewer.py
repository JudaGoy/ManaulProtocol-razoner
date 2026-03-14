import customtkinter as ctk
import os
from tkinter import scrolledtext
from typing import List

from core.change_parser import Change, ChangeError, apply_change, get_file_diff


class ChangeReviewerWindow(ctk.CTkToplevel):
    def __init__(self, parent, project_path: str, changes: List[Change]):
        super().__init__(parent)
        
        self.title("Revisor de Cambios")
        self.geometry("1000x700")
        
        self.project_path = project_path
        self.changes = changes
        self.change_widgets = {}
        
        self.setup_ui()
        self.load_changes()
    
    def setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        header = ctk.CTkFrame(self)
        header.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        
        ctk.CTkLabel(
            header,
            text=f"📋 Cambios detectados: {len(self.changes)}",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(side="left", padx=10)
        
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
        
        self.changes_container = ctk.CTkScrollableFrame(self)
        self.changes_container.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        
        self.status_frame = ctk.CTkFrame(self)
        self.status_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=10)
        
        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="Esperando acciones...",
            font=ctk.CTkFont(size=12)
        )
        self.status_label.pack(pady=5)
    
    def load_changes(self):
        for i, change in enumerate(self.changes):
            card = self.create_change_card(change, i)
            card.pack(fill="x", pady=5, padx=5)
    
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
        
        position_text = ""
        if change.position_type == 'inicio':
            position_text = "al inicio"
        elif change.position_type == 'final':
            position_text = "al final"
        elif change.start_line and change.end_line:
            position_text = f"líneas {change.start_line}-{change.end_line}"
        elif change.start_line:
            position_text = f"línea {change.start_line}"
        
        ctk.CTkLabel(
            header,
            text=f"{action_text} {position_text}",
            font=ctk.CTkFont(size=12)
        ).pack(side="right")
        
        diff_frame = ctk.CTkFrame(card)
        diff_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        old_lines, new_lines = get_file_diff(change)
        
        diff_text = scrolledtext.ScrolledText(
            diff_frame,
            height=10,
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
            
            if not old_lines and change.position_type in ['inicio', 'final']:
                diff_content = "+++ Código nuevo (+):\n"
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
        widget_data = self.change_widgets[index]
        
        if not widget_data['accepted']:
            success = apply_change(widget_data['change'])
            
            if success:
                widget_data['accepted'] = True
                widget_data['card'].configure(fg_color="#1a3d1a")
                self.update_status()
            else:
                self.show_error(f"No se pudo aplicar el cambio {index + 1}")
    
    def reject_change(self, index):
        widget_data = self.change_widgets[index]
        widget_data['card'].configure(fg_color="#3d1a1a")
        self.update_status()
    
    def accept_all(self):
        accepted_count = 0
        for i, widget_data in self.change_widgets.items():
            if not widget_data['accepted']:
                success = apply_change(widget_data['change'])
                if success:
                    widget_data['accepted'] = True
                    widget_data['card'].configure(fg_color="#1a3d1a")
                    accepted_count += 1
        
        self.update_status()
        self.show_info(f"Se aplicaron {accepted_count} cambios")
    
    def reject_all(self):
        for widget_data in self.change_widgets.values():
            widget_data['card'].configure(fg_color="#3d1a1a")
        self.update_status()
    
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
        error_win.geometry("300x100")
        
        ctk.CTkLabel(error_win, text=f"❌ {message}").pack(expand=True)
        ctk.CTkButton(error_win, text="Aceptar", command=error_win.destroy).pack(pady=5)
    
    def show_info(self, message):
        info_win = ctk.CTkToplevel(self)
        info_win.title("Información")
        info_win.geometry("300x100")
        
        ctk.CTkLabel(info_win, text=f"ℹ️ {message}").pack(expand=True)
        ctk.CTkButton(info_win, text="Aceptar", command=info_win.destroy).pack(pady=5)
