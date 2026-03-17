from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading
import os


class ProjectWatcher:
    def __init__(self, path, callback):
        self.path = path
        self.callback = callback
        self.ignorar = False
        self.observer = None
        self.lock = threading.Lock()
        self._historial_dir = os.path.join(path, '.apply_history')
        self.ignore_patterns = {'.apply_history', '__pycache__', '.git', '.pyc', '.pyo', '.DS_Store'}
    
    def iniciar(self):
        self.observer = Observer()
        handler = ChangeHandler(self)
        self.observer.schedule(handler, self.path, recursive=True)
        self.observer.start()
    
    def detener(self):
        if self.observer:
            self.observer.stop()
            self.observer.join()
    
    def debe_ignorar(self, filepath):
        with self.lock:
            if self.ignorar:
                return True
        
        for pattern in self.ignore_patterns:
            if pattern in filepath:
                return True
        
        return False
    
    def on_created(self, filepath):
        if self.debe_ignorar(filepath):
            return
        
        self.callback()


class ChangeHandler(FileSystemEventHandler):
    def __init__(self, watcher):
        self.watcher = watcher
    
    def on_created(self, event):
        self.watcher.on_created(event.src_path)
    
    def on_deleted(self, event):
        self.watcher.on_created(event.src_path)
