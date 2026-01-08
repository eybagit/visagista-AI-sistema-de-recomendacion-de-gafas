"""
Servicio para gestión de imágenes con Cloudinary
"""
import os
import cloudinary
import cloudinary.uploader
import base64
import uuid

# Configurar Cloudinary desde CLOUDINARY_URL
cloudinary.config(
    cloudinary_url=os.getenv('CLOUDINARY_URL')
)

def upload_selfie(image_data, filename=None):
    """
    Sube una imagen a Cloudinary y retorna la URL pública
    
    Args:
        image_data: Datos de la imagen (base64 string o file path)
        filename: Nombre base para el archivo (opcional)
    
    Returns:
        dict: Información de la imagen subida incluyendo URL pública
    """
    try:
        # Generar nombre único si no se proporciona
        if filename is None:
            filename = f"selfie_{uuid.uuid4().hex[:8]}"
        
        # Si es base64, preparar para upload
        if isinstance(image_data, str) and image_data.startswith('data:image'):
            # Ya está en formato data URI, Cloudinary lo acepta directamente
            upload_data = image_data
        elif isinstance(image_data, str) and not os.path.exists(image_data):
            # Es base64 sin prefijo, agregar prefijo
            upload_data = f"data:image/jpeg;base64,{image_data}"
        else:
            upload_data = image_data
        
        # Subir imagen a Cloudinary
        upload_result = cloudinary.uploader.upload(
            upload_data,
            folder="glasses-selfies",
            public_id=filename,
            overwrite=True,
            resource_type="image"
        )
        
        return {
            "success": True,
            "url": upload_result.get('secure_url'),
            "public_id": upload_result.get('public_id'),
            "width": upload_result.get('width'),
            "height": upload_result.get('height')
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def delete_selfie(public_id):
    """
    Elimina una imagen de Cloudinary
    
    Args:
        public_id: ID público de la imagen en Cloudinary
    
    Returns:
        dict: Resultado de la operación
    """
    try:
        result = cloudinary.uploader.destroy(public_id)
        return {
            "success": True,
            "result": result
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
