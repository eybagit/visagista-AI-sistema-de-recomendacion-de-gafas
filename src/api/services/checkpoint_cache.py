"""
Módulo de Checkpoint Cache para Análisis de Gafas
Guarda progreso de generación para poder resumir si falla
"""

import hashlib
import json
import os
from datetime import datetime, timedelta

# Directorio para almacenar checkpoints
CACHE_DIR = os.path.join(os.path.dirname(__file__), '.cache')
CACHE_TTL_HOURS = 1  # Tiempo de vida del caché en horas


def _ensure_cache_dir():
    """Crea el directorio de caché si no existe"""
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)
        print(f"[CACHE] Directorio de caché creado: {CACHE_DIR}")


def get_session_id(selfie_url):
    """
    Genera un ID de sesión único basado en la URL de la selfie.
    La misma imagen siempre genera el mismo ID.
    
    Args:
        selfie_url: URL de la selfie en Cloudinary
    
    Returns:
        str: Hash MD5 truncado de 12 caracteres
    """
    return hashlib.md5(selfie_url.encode()).hexdigest()[:12]


def _get_cache_path(session_id, key):
    """Genera la ruta del archivo de caché"""
    return os.path.join(CACHE_DIR, f"{session_id}_{key}.json")


def _is_expired(timestamp_str):
    """Verifica si un timestamp ha expirado según el TTL"""
    try:
        cached_time = datetime.fromisoformat(timestamp_str)
        expiry_time = cached_time + timedelta(hours=CACHE_TTL_HOURS)
        return datetime.now() > expiry_time
    except:
        return True


def get_checkpoint(session_id, key):
    """
    Recupera un checkpoint si existe y no ha expirado.
    
    Args:
        session_id: ID de sesión (del hash de selfie URL)
        key: Clave del checkpoint (ej: 'analysis', 'styles', 'img_on_face_0')
    
    Returns:
        El valor cacheado o None si no existe/expiró
    """
    _ensure_cache_dir()
    cache_path = _get_cache_path(session_id, key)
    
    if not os.path.exists(cache_path):
        return None
    
    try:
        with open(cache_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Verificar expiración
        if _is_expired(data.get('timestamp', '')):
            print(f"[CACHE] Checkpoint expirado: {key}")
            os.remove(cache_path)
            return None
        
        print(f"[CACHE] ✓ Recuperado checkpoint: {key}")
        return data.get('value')
    
    except Exception as e:
        print(f"[CACHE] Error leyendo checkpoint {key}: {e}")
        return None


def save_checkpoint(session_id, key, value):
    """
    Guarda un checkpoint con timestamp.
    
    Args:
        session_id: ID de sesión
        key: Clave del checkpoint
        value: Valor a guardar (debe ser serializable a JSON)
    
    Returns:
        bool: True si se guardó correctamente
    """
    _ensure_cache_dir()
    cache_path = _get_cache_path(session_id, key)
    
    try:
        data = {
            'timestamp': datetime.now().isoformat(),
            'session_id': session_id,
            'key': key,
            'value': value
        }
        
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)
        
        print(f"[CACHE] ✓ Guardado checkpoint: {key}")
        return True
    
    except Exception as e:
        print(f"[CACHE] Error guardando checkpoint {key}: {e}")
        return False


def clear_session(session_id):
    """
    Limpia todos los checkpoints de una sesión.
    Útil después de completar exitosamente.
    
    Args:
        session_id: ID de sesión a limpiar
    """
    _ensure_cache_dir()
    
    deleted_count = 0
    for filename in os.listdir(CACHE_DIR):
        if filename.startswith(session_id):
            try:
                os.remove(os.path.join(CACHE_DIR, filename))
                deleted_count += 1
            except:
                pass
    
    if deleted_count > 0:
        print(f"[CACHE] Limpiados {deleted_count} checkpoints de sesión {session_id}")


def get_session_status(session_id):
    """
    Obtiene el estado actual de una sesión (qué checkpoints existen).
    
    Args:
        session_id: ID de sesión
    
    Returns:
        dict: Estado de cada tipo de checkpoint
    """
    _ensure_cache_dir()
    
    status = {
        'analysis': False,
        'styles': False,
        'specs_0': False,
        'specs_1': False,
        'img_on_face_0': False,
        'img_product_0': False,
        'img_on_face_1': False,
        'img_product_1': False
    }
    
    for key in status.keys():
        cache_path = _get_cache_path(session_id, key)
        if os.path.exists(cache_path):
            cached = get_checkpoint(session_id, key)
            status[key] = cached is not None
    
    return status


def cleanup_expired():
    """
    Limpia todos los checkpoints expirados del directorio de caché.
    Útil para mantenimiento periódico.
    """
    _ensure_cache_dir()
    
    deleted_count = 0
    for filename in os.listdir(CACHE_DIR):
        if filename.endswith('.json'):
            filepath = os.path.join(CACHE_DIR, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if _is_expired(data.get('timestamp', '')):
                    os.remove(filepath)
                    deleted_count += 1
            except:
                pass
    
    if deleted_count > 0:
        print(f"[CACHE] Limpiados {deleted_count} checkpoints expirados")
