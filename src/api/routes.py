"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
from flask import Flask, request, jsonify, url_for, Blueprint, Response, stream_with_context
from api.models import db, User
from api.utils import generate_sitemap, APIException
from api.services.cloudinary_service import upload_selfie
from api.services.gemini_service import analyze_face_for_glasses
from api.services.progress_tracker import create_tracker, get_tracker, cleanup_tracker
from flask_cors import CORS
import json
import time

api = Blueprint('api', __name__)

# Allow CORS requests to this API
CORS(api)


@api.route('/hello', methods=['POST', 'GET'])
def handle_hello():

    response_body = {
        "message": "Hello! I'm a message that came from the backend, check the network tab on the google inspector and you will see the GET request"
    }

    return jsonify(response_body), 200


@api.route('/analyze-progress/<session_id>', methods=['GET'])
def analyze_progress(session_id):
    """
    Endpoint SSE para streaming de progreso del análisis
    """
    def generate():
        tracker = get_tracker(session_id)
        if not tracker:
            yield f"data: {{\"error\": \"Session not found\"}}\n\n"
            return
        
        last_progress = -1
        
        while True:
            progress_data = tracker.get_progress()
            current_progress = progress_data['progress']
            
            # Solo enviar si hay cambio
            if current_progress != last_progress:
                yield f"data: {json.dumps(progress_data)}\n\n"
                last_progress = current_progress
            
            # Terminar cuando llegue a 100%
            if current_progress >= 100:
                break
            
            time.sleep(0.5)  # Actualizar cada 500ms
        
        # Limpiar tracker después de completar
        cleanup_tracker(session_id)
    
    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no'
        }
    )


@api.route('/analyze-face', methods=['POST'])
def analyze_face():
    """
    Endpoint SSE para analizar selfie y recomendar monturas.
    Envía resultados PROGRESIVAMENTE a medida que llegan.
    
    Flujo:
    1. Sube imagen a Cloudinary
    2. Envía análisis de texto (primero, más rápido)
    3. Envía imágenes una a una
    4. Envía resumen final con costos
    """
    try:
        print("[API] Recibiendo request /analyze-face (streaming)")
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No se recibieron datos"}), 400
        
        image_data = data.get('image')
        user_data = data.get('userData', {})
        
        if not image_data:
            return jsonify({"error": "No se recibió imagen"}), 400
        
        def generate():
            from api.services.gemini_service import generate_text_analysis, generate_glasses_images
            
            # Capturar variables del scope exterior
            img_data = image_data
            usr_data = user_data
            
            total_usage = {
                "prompt_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0,
                "image_generations": 0,
                "text_generations": 0,
                "processing_time_seconds": 0
            }
            start_time = time.time()
            
            # === PASO 1: Subir imagen a Cloudinary ===
            progress_data = {"type": "progress", "status": "Subiendo imagen...", "progress": 5}
            yield f"data: {json.dumps(progress_data)}\n\n"
            
            upload_result = upload_selfie(img_data)
            
            if not upload_result["success"]:
                err_msg = upload_result.get("error", "Error desconocido")
                error_data = {"type": "error", "error": f"Error subiendo imagen: {err_msg}"}
                yield f"data: {json.dumps(error_data)}\n\n"
                return
            
            selfie_url = upload_result["url"]
            print(f"[API] Imagen subida: {selfie_url}")
            
            selfie_data = {"type": "selfie", "selfie_url": selfie_url}
            yield f"data: {json.dumps(selfie_data)}\n\n"
            
            progress_data = {"type": "progress", "status": "Analizando tu rostro...", "progress": 15}
            yield f"data: {json.dumps(progress_data)}\n\n"
            
            # === PASO 2: Análisis de texto (más rápido) ===
            print("[API] Generando análisis de texto...")
            text_result = generate_text_analysis(selfie_url, usr_data)
            
            text_time = time.time() - start_time
            print(f"[API] Texto completado en {text_time:.2f}s")
            
            if text_result.get("success"):
                # Agregar tokens de texto
                if text_result.get("usage"):
                    total_usage["prompt_tokens"] += text_result["usage"].get("prompt_tokens", 0)
                    total_usage["output_tokens"] += text_result["usage"].get("output_tokens", 0)
                    total_usage["total_tokens"] += text_result["usage"].get("total_tokens", 0)
                    total_usage["text_generations"] = 1
                
                analysis_data = {"type": "analysis", "analysis": text_result.get("analysis", "")}
                yield f"data: {json.dumps(analysis_data)}\n\n"
            else:
                error_data = {"type": "analysis_error", "error": text_result.get("error")}
                yield f"data: {json.dumps(error_data)}\n\n"
            
            progress_data = {"type": "progress", "status": "Generando monturas...", "progress": 50}
            yield f"data: {json.dumps(progress_data)}\n\n"
            
            # === PASO 3: Generar imágenes con entrega progresiva REAL ===
            # Usamos threading + queue para poder yield imágenes conforme se generan
            print("[API] Generando imágenes (entrega progresiva)...")
            
            import threading
            from queue import Queue, Empty
            
            image_queue = Queue()
            result_holder = [None]  # Para capturar resultado final en el thread
            
            def run_generation():
                """Thread que genera imágenes y las pone en la queue"""
                def on_image_ready(image_data, index):
                    print(f"[API] ✓ Imagen {index + 1}/4 generada, enviando al cliente...")
                    image_queue.put(("image", image_data, index))
                
                result = generate_glasses_images(selfie_url, usr_data, on_image_generated=on_image_ready)
                result_holder[0] = result
                image_queue.put(("done", result, None))  # Señal de finalización
            
            # Iniciar generación en thread separado
            gen_thread = threading.Thread(target=run_generation)
            gen_thread.start()
            
            images_sent = 0
            
            # Consumir imágenes de la queue y enviarlas vía SSE
            while True:
                try:
                    # Esperar hasta 1 segundo por cada item
                    item = image_queue.get(timeout=1.0)
                    event_type, data, index = item
                    
                    if event_type == "image":
                        images_sent += 1
                        progress = 50 + images_sent * 12
                        
                        # Enviar imagen inmediatamente
                        img_event_data = {"type": "image", "image": data, "index": index}
                        yield f"data: {json.dumps(img_event_data)}\n\n"
                        
                        progress_data = {"type": "progress", "status": f"Imagen {images_sent}/4 enviada", "progress": progress}
                        yield f"data: {json.dumps(progress_data)}\n\n"
                        
                        print(f"[API] ✓ Imagen {images_sent}/4 enviada al cliente")
                    
                    elif event_type == "done":
                        # Generación completada
                        images_result = data
                        break
                        
                except Empty:
                    # Timeout, verificar si el thread sigue vivo
                    if not gen_thread.is_alive():
                        images_result = result_holder[0]
                        break
                    continue
            
            # Esperar a que el thread termine
            gen_thread.join(timeout=5.0)
            
            images_time = time.time() - start_time
            print(f"[API] Imágenes completadas en {images_time:.2f}s ({images_sent} enviadas progresivamente)")
            
            # Agregar tokens de imágenes al total
            if images_result and images_result.get("success") and images_result.get("usage"):
                total_usage["prompt_tokens"] += images_result["usage"].get("prompt_tokens", 0)
                total_usage["output_tokens"] += images_result["usage"].get("output_tokens", 0)
                total_usage["total_tokens"] += images_result["usage"].get("total_tokens", 0)
                total_usage["image_generations"] = images_result["usage"].get("image_generations", 0)
            elif images_result and not images_result.get("success"):
                error_data = {"type": "images_error", "error": images_result.get("error")}
                yield f"data: {json.dumps(error_data)}\n\n"
            
            # === PASO 4: Enviar resumen final ===
            total_usage["processing_time_seconds"] = round(time.time() - start_time, 2)
            
            usage_data = {"type": "usage", "usage": total_usage}
            yield f"data: {json.dumps(usage_data)}\n\n"
            
            complete_data = {"type": "complete", "success": True, "progress": 100}
            yield f"data: {json.dumps(complete_data)}\n\n"
            
            print(f"[API] Streaming completado en {total_usage['processing_time_seconds']}s")
        
        return Response(
            stream_with_context(generate()),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no',
                'Access-Control-Allow-Origin': '*'
            }
        )
        
    except Exception as e:
        import traceback
        print(f"[API ERROR] {str(e)}")
        print(f"[API ERROR] Traceback: {traceback.format_exc()}")
        return jsonify({
            "error": f"Error interno: {str(e)}"
        }), 500


