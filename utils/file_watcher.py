from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading
import os
import subprocess


class ProjectWatcher:
    def __init__(self, path, callback, commit_callback=None):
        self.path = path
        self.callback = callback
        self.commit_callback = commit_callback
        self.ignorar = False
        self.observer = None
        self.lock = threading.Lock()
        self.ignore_patterns = {'.apply_history', '__pycache__', '.git', '.pyc', '.pyo', '.DS_Store'}
        self.last_commit_hash = self._get_current_commit_hash()
    
    def _run_git_command(self, *args):
        try:
            result = subprocess.run(
                ['git'] + list(args),
                cwd=self.path,
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.stdout.strip(), result.returncode
        except Exception:
            return "", 1
    
    def _get_current_commit_hash(self):
        stdout, code = self._run_git_command('rev-parse', 'HEAD')
        if code == 0 and stdout:
            return stdout
        return ""
    
    def _get_files_in_last_commit(self):
        stdout, code = self._run_git_command('diff-tree', '--no-commit-id', '--name-only', '-r', 'HEAD')
        if code == 0 and stdout:
            return [f.strip() for f in stdout.split('\n') if f.strip()]
        return []
    
    def _check_for_new_commit(self):
        current_hash = self._get_current_commit_hash()
        if current_hash and current_hash != self.last_commit_hash:
            self.last_commit_hash = current_hash
            return True
        return False
    
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
        
        if self.commit_callback and self._check_for_new_commit():
            files = self._get_files_in_last_commit()
            self.commit_callback(files)
        else:
            self.callback()
    
    def on_deleted(self, filepath):
        if self.debe_ignorar(filepath):
            return
        
        if self.commit_callback and self._check_for_new_commit():
            files = self._get_files_in_last_commit()
            self.commit_callback(files)
        else:
            self.callback()
    
    def check_commit(self):
        if self.commit_callback and self._check_for_new_commit():
            files = self._get_files_in_last_commit()
            self.commit_callback(files)


class ChangeHandler(FileSystemEventHandler):
    def __init__(self, watcher):
        self.watcher = watcher
    
    def on_created(self, event):
        self.watcher.on_created(event.src_path)
    
    def on_deleted(self, event):
        self.watcher.on_deleted(event.src_path)
