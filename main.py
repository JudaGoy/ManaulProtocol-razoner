from ui.windows.main_window import AICodeEditor

if __name__ == "__main__":
    app = AICodeEditor()
    app.protocol("WM_DELETE_WINDOW", lambda: (app.detener_watcher() if hasattr(app, 'watcher') and app.watcher else None, app.destroy()))
    app.mainloop()
