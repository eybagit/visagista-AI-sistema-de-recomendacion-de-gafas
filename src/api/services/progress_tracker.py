"""
Utilidad para tracking de progreso en tiempo real
Usa un sistema de eventos para reportar progreso al frontend
"""
import time
from threading import Lock
import uuid

class ProgressTracker:
    """Rastrea el progreso de operaciones asíncronas"""
    
    def __init__(self):
        self.progress = 0
        self.status = "Iniciando..."
        self.lock = Lock()
        self.start_time = None
        self.estimated_total = 60  # segundos estimados
    
    def start(self):
        """Inicia el tracking"""
        with self.lock:
            self.start_time = time.time()
            self.progress = 0
            self.status = "Iniciando análisis..."
    
    def update(self, progress, status):
        """Actualiza el progreso (0-100)"""
        with self.lock:
            self.progress = min(100, max(0, progress))
            self.status = status
    
    def get_progress(self):
        """Obtiene el progreso actual"""
        with self.lock:
            elapsed = time.time() - self.start_time if self.start_time else 0
            # Estimar progreso basado en tiempo si no se ha actualizado manualmente
            if self.progress < 95:
                time_based_progress = min(90, (elapsed / self.estimated_total) * 100)
                actual_progress = max(self.progress, time_based_progress)
            else:
                actual_progress = self.progress
            
            return {
                "progress": int(actual_progress),
                "status": self.status,
                "elapsed": int(elapsed)
            }
    
    def complete(self):
        """Marca como completado"""
        with self.lock:
            self.progress = 100
            self.status = "Completado"

# Diccionario global de trackers por session_id
_trackers = {}
_trackers_lock = Lock()

def create_tracker():
    """Crea un nuevo tracker con un ID único"""
    session_id = str(uuid.uuid4())
    with _trackers_lock:
        _trackers[session_id] = ProgressTracker()
    return session_id, _trackers[session_id]

def get_tracker(session_id):
    """Obtiene un tracker por su session_id"""
    with _trackers_lock:
        return _trackers.get(session_id)

def cleanup_tracker(session_id):
    """Elimina un tracker cuando ya no se necesita"""
    with _trackers_lock:
        if session_id in _trackers:
            del _trackers[session_id]

