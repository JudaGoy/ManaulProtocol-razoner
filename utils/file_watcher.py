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
        
        if '.apply_history' in filepath:
            return True
        
        if '__pycache__' in filepath:
            return True
        
        if filepath.endswith('.pyc'):
            return True
        
        return False
    
    def on_change(self, filepath):
        if self.debe_ignorar(filepath):
            return
        
        self.callback()


class ChangeHandler(FileSystemEventHandler):
    def __init__(self, watcher):
        self.watcher = watcher
    
    def on_modified(self, event):
        if not event.is_directory:
            self.watcher.on_change(event.src_path)
    
    def on_created(self, event):
        if not event.is_directory:
            self.watcher.on_change(event.src_path)
