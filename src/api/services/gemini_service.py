"""
Servicio para comunicación con Google Gemini AI via Vertex AI
Modelos:
- gemini-2.5-flash-image: Generación de imágenes
- gemini-2.5-flash: Análisis de texto

Usa el SDK google-genai con Vertex AI
"""
import os
import base64
import requests

# Importar sistema de checkpoints
from .checkpoint_cache import (
    get_session_id, 
    get_checkpoint, 
    save_checkpoint, 
    clear_session,
    get_session_status
)

from google import genai
from google.genai import types

# Configurar cliente con API Key (más simple que Vertex AI)
# Solo requiere: GOOGLE_API_KEY en .env
# Los modelos gemini-2.5-flash-* funcionan igual con API Key
client = genai.Client(api_key=os.getenv('GOOGLE_API_KEY'))

# Modelos a utilizar
IMAGE_MODEL = "gemini-2.5-flash-image"
TEXT_MODEL = "gemini-2.5-flash"

# Prompt ADAPTATIVO para generar imagen de la MONTURA EN EL ROSTRO de la persona
# Ahora incluye especificaciones detalladas para garantizar consistencia
GLASSES_ON_FACE_PROMPT = """
You are a professional eyewear photo editor.

TASK: Add eyeglasses to this person's face.

GLASSES SPECIFICATIONS:
Create glasses with THESE EXACT SPECIFICATIONS:
{detailed_specs}

CRITICAL REQUIREMENTS:
1. COLOR: Use the EXACT color/finish specified above - do NOT change or interpret
2. THICKNESS: Use the EXACT thickness specified
3. MATERIAL: Use the EXACT material and finish described
4. ORIENTATION: Generate image in VERTICAL/PORTRAIT orientation (height greater than width)
5. ASPECT RATIO: Use typical selfie aspect ratio (3:4 or 9:16 portrait orientation)

EAR DETECTION & TEMPLE PLACEMENT (MOST CRITICAL):
6. ANALYZE EARS: First, carefully identify the exact position of the person's ears in the photo
7. TEMPLE ANCHOR POINT: Temple arms MUST terminate exactly at the ear position visible in the photo
8. NO FLOATING: Temple arms must NOT float in the air - they MUST physically rest on top of the ears
9. EAR HOOK: If ears are visible, temple tips must curve BEHIND and DOWN around the ear
10. HIDDEN EARS: If ears are partially hidden by hair, estimate ear position from eye-to-ear distance and ensure temples reach that point
11. NATURAL WEIGHT: Glasses must appear to have weight resting on the ears, not hovering

ANATOMICAL POSITIONING:
12. BRIDGE ALIGNMENT: Position bridge precisely on nose bridge, centered between eyes
13. EYE ALIGNMENT: Frame should sit at natural eye level, not too high or low
14. HORIZONTAL LEVEL: Frame must be perfectly horizontal, parallel to eye line
15. NATURAL FIT: Glasses should appear as if actually worn for hours, fully settled on face

REALISM REQUIREMENTS:
16. PROPORTIONS: Scale to fit face width naturally (temples aligned with face edges)
17. PERSPECTIVE: Match camera angle and head rotation from the original photo
18. LIGHTING: Replicate lighting direction, shadows, reflections from original photo
19. DETAILS: Add subtle lens reflections, natural shadows under frames, visible temple arms going TO the ears
20. PRESERVATION: Keep face, hair, skin, background COMPLETELY UNCHANGED

OUTPUT: Single photorealistic image showing the person wearing the specified glasses.
The glasses MUST appear naturally positioned as if the person is actually wearing them.
Temple arms MUST be visible going to and resting on the ears, NOT floating in mid-air.
The output image MUST be in VERTICAL/PORTRAIT orientation (taller than wide).
DO NOT change facial features, expression, pose, or background.
DO NOT add text, labels, or multiple views.
Generate EXACTLY ONE vertical portrait image.
"""

# Prompt ADAPTATIVO para generar imagen de la MONTURA SOLA (producto)
# Ahora incluye especificaciones detalladas para garantizar mismo color que rostro
GLASSES_PRODUCT_PROMPT = """
You are a professional product photographer for an eyewear e-commerce catalog.

TASK: Create a product photograph of eyeglasses.

GLASSES SPECIFICATIONS:
Create a product photo of THESE EXACT SAME GLASSES:
{detailed_specs}

CRITICAL REQUIREMENTS:
1. COLOR: Use the EXACT color/finish specified above - this MUST match perfectly
2. THICKNESS: Use the EXACT thickness specified
3. MATERIAL: Use the EXACT material and finish described
4. CONSISTENCY: Every detail must match the specifications exactly

PHOTOGRAPHY REQUIREMENTS:
1. ANGLE: 3/4 view showing both front and side profile
2. POSITION: Floating/suspended, slightly tilted to showcase shape
3. LIGHTING: Professional studio lighting, soft shadows, subtle highlights
4. LENSES: Clear transparent with minimal realistic reflections
5. BACKGROUND: Pure white or light gray gradient, clean and empty
6. QUALITY: Ultra-high resolution, commercial catalog quality

CRITICAL EXCLUSIONS:
- NO human face, head, or body parts
- NO hands holding glasses
- NO text, labels, prices, or brand names
- NO multiple glasses or alternative views
- NO props or display stands

OUTPUT: Single premium product photograph showing ONLY the specified eyeglasses.
Generate EXACTLY ONE image.
"""


TEXT_ANALYSIS_PROMPT = """
Eres un estilista óptico que ayuda a clientes a elegir sus gafas perfectas.

Analiza la selfie del cliente y genera un RESUMEN BREVE y AMIGABLE para ayudarle a comprar.

## INSTRUCCIONES:
- Sé conciso y directo (máximo 300 palabras total)
- Usa un tono cálido y personal
- Enfócate en lo que MÁS le favorece
- NO uses términos técnicos complejos

## FORMATO DE RESPUESTA:

### 👤 Tu Perfil
Una oración describiendo tu tipo de rostro y tono de piel.

### ✨ Lo Que Te Favorece
- 3 características clave que debes buscar en tus gafas (bullet points cortos)

### 🎯 Mis 2 Recomendaciones Top

**1. [Nombre del Estilo]** - [Material]
Color recomendado: [color]
Por qué te queda bien: [1 oración]

**2. [Nombre del Estilo]** - [Material]  
Color recomendado: [color]
Por qué te queda bien: [1 oración]

### ⚠️ Evita
Un bullet point con lo que NO te favorece.

### 💡 Tip Final
Un consejo práctico de compra en 1 oración.

---
Responde en español, amigable y listo para que el cliente tome una decisión de compra rápida.
"""

def format_user_data(user_data):
    """Formatea los datos del usuario para el prompt"""
    formatted = []
    
    # Datos biométricos
    if user_data.get('genero'):
        formatted.append(f"- Género: {user_data['genero']}")
    if user_data.get('edad'):
        formatted.append(f"- Edad: {user_data['edad']}")
    if user_data.get('estatura'):
        formatted.append(f"- Estatura: {user_data['estatura']}")
    
    # Auto-percepción de rasgos
    if user_data.get('formaMandibula'):
        formatted.append(f"- Forma de Mandíbula: {user_data['formaMandibula']}")
    if user_data.get('frente'):
        formatted.append(f"- Frente: {user_data['frente']}")
    if user_data.get('narizPuente'):
        formatted.append(f"- Nariz/Puente: {user_data['narizPuente']}")
    if user_data.get('tonoPiel'):
        formatted.append(f"- Tono de Piel: {user_data['tonoPiel']}")
    if user_data.get('colorCabello'):
        formatted.append(f"- Color de Cabello: {user_data['colorCabello']}")
    if user_data.get('colorOjos'):
        formatted.append(f"- Color de Ojos: {user_data['colorOjos']}")
    
    # Estilo de vida
    if user_data.get('usoPrincipal'):
        formatted.append(f"- Uso Principal: {user_data['usoPrincipal']}")
    if user_data.get('estiloDeseado'):
        formatted.append(f"- Estilo Deseado: {user_data['estiloDeseado']}")
    if user_data.get('materialPreferido'):
        formatted.append(f"- Material Preferido: {user_data['materialPreferido']}")
    if user_data.get('exclusiones'):
        formatted.append(f"- No desea: {user_data['exclusiones']}")
    
    return "\n".join(formatted)

def select_best_frame_styles(image_bytes, all_styles):
    """
    La IA analiza el rostro y selecciona los 2 estilos más favorecedores de 10 opciones.
    
    Args:
        image_bytes: Bytes de la imagen selfie
        all_styles: Lista con los 10 estilos disponibles
    
    Returns:
        list: Los 2 estilos seleccionados (o todos si falla)
    """
    try:
        print(f"[DEBUG] Solicitando a la IA que seleccione los 2 mejores estilos de {len(all_styles)} opciones...")
        
        # Construir lista de opciones para el prompt
        styles_list = "\n".join([
            f"{i+1}. **{s['name']}** ({s['style']}): {s['description']}"
            for i, s in enumerate(all_styles)
        ])
        
        selection_prompt = f"""You are an expert eyewear stylist analyzing a client's face.

STEP 1 - ANALYZE THIS PERSON'S FACE:
Carefully observe:
- Face shape (oval, round, square, heart-shaped, diamond, oblong, triangular)
- Facial proportions (face width, face length, jawline width, forehead width)
- Features (eyes distance, nose bridge width, cheekbone prominence)
- Overall aesthetic (professional, casual, artistic, sporty, elegant)

STEP 2 - SELECT THE 2 BEST FRAME STYLES:
From these 10 eyeglass frame options, select the 2 styles that will be MOST FLATTERING for this specific person:

{styles_list}

SELECTION CRITERIA:
- Face shape compatibility (frames should complement, not mirror face shape)
- Proportional balance (frame size should match face size)
- Style coherence (match their apparent lifestyle/aesthetic)
- Versatility (at least one versatile option, one bold option)

STEP 3 - RESPOND:
Respond with ONLY the 2 numbers (1-10) of your selected styles, separated by comma.
Example response: "3, 7"

DO NOT include explanations, just the two numbers.
"""
        
        # Crear parte de imagen
        image_part = types.Part.from_bytes(
            data=image_bytes,
            mime_type="image/png"
        )
        
        # Generar respuesta
        response = client.models.generate_content(
            model=TEXT_MODEL,
            contents=[selection_prompt, image_part]
        )
        
        # Extraer respuesta de texto
        selection_text = ""
        if hasattr(response, 'text'):
            selection_text = response.text
        elif hasattr(response, 'candidates') and response.candidates:
            for candidate in response.candidates:
                if hasattr(candidate, 'content') and candidate.content:
                    for part in candidate.content.parts:
                        if hasattr(part, 'text') and part.text:
                            selection_text += part.text
        
        print(f"[DEBUG] Respuesta de selección de IA: {selection_text.strip()}")
        
        # Parsear números seleccionados
        import re
        numbers = re.findall(r'\d+', selection_text)
        if len(numbers) >= 2:
            idx1 = int(numbers[0]) - 1  # Convertir de 1-indexed a 0-indexed
            idx2 = int(numbers[1]) - 1
            
            # Validar índices
            if 0 <= idx1 < len(all_styles) and 0 <= idx2 < len(all_styles) and idx1 != idx2:
                selected = [all_styles[idx1], all_styles[idx2]]
                print(f"[SUCCESS] IA seleccionó: {selected[0]['name']} y {selected[1]['name']}")
                return selected
        
        # Si falla el parseo, usar los primeros 2 por defecto
        print(f"[WARN] No se pudo parsear selección, usando primeros 2 estilos por defecto")
        return all_styles[:2]
        
    except Exception as e:
        print(f"[ERROR] Error en selección de estilos: {str(e)}")
        print(f"[WARN] Usando primeros 2 estilos por defecto")
        return all_styles[:2]

def design_glasses_specifications(image_bytes, frame_style_info):
    """
    La IA analiza el rostro y diseña especificaciones detalladas de las gafas EN TEXTO.
    Esto garantiza que el color y detalles sean idénticos en rostro y producto.
    
    Args:
        image_bytes: Bytes de la imagen selfie
        frame_style_info: Dict con info del estilo (name, style, description)
    
    Returns:
        str: Descripción detallada de las gafas diseñadas
    """
    try:
        print(f"[DEBUG] Diseñando especificaciones para {frame_style_info['name']}...")
        
        design_prompt = f"""You are an expert eyewear designer analyzing this client's face.

STEP 1 - ANALYZE THE FACE:
Observe this person's:
- Face shape and proportions
- Skin tone (warm/cool/neutral undertones)
- Hair color and eye color
- Overall style aesthetic

STEP 2 - DESIGN {frame_style_info['style'].upper()} GLASSES:
Based on your analysis, design the perfect {frame_style_info['style']} eyeglasses for this person.

Choose EXACT specifications:
- **Exact color/finish**: Be very specific (e.g., "brushed gold", "matte black", "tortoiseshell brown with amber flecks", "gunmetal gray", "rose gold", "navy blue acetate", etc.)
- **Frame thickness**: Specify exact thickness (e.g., "thin 1mm", "medium 2-3mm", "thick 4-5mm")
- **Material details**: Describe material finish (e.g., "matte finish", "glossy polish", "brushed metal")
- **Lens tint**: Clear or subtle tint
- **Temple arms design**: Shape and finish

STEP 3 - RESPOND:
Provide a SINGLE PARAGRAPH detailed description of the glasses you designed.
Start directly with the description, no preamble.

Example format:
"Brushed gold rectangular metal frames with thin 1.5mm construction, featuring a matte finish that complements the warm skin tone. Clear transparent lenses with anti-reflective coating. Straight temple arms in matching brushed gold with subtle flex hinges."

Your detailed description:"""

        # Crear parte de imagen
        image_part = types.Part.from_bytes(
            data=image_bytes,
            mime_type="image/png"
        )
        
        # Generar especificaciones
        response = client.models.generate_content(
            model=TEXT_MODEL,
            contents=[design_prompt, image_part]
        )
        
        # Extraer descripción
        description = ""
        if hasattr(response, 'text'):
            description = response.text
        elif hasattr(response, 'candidates') and response.candidates:
            for candidate in response.candidates:
                if hasattr(candidate, 'content') and candidate.content:
                    for part in candidate.content.parts:
                        if hasattr(part, 'text') and part.text:
                            description += part.text
        
        description = description.strip()
        print(f"[DEBUG] Diseño creado: {description[:100]}...")
        return description
        
    except Exception as e:
        print(f"[ERROR] Error diseñando especificaciones: {str(e)}")
        # Descripción genérica de fallback
        return f"{frame_style_info['style']} eyeglasses with professional finish"

def download_image_as_bytes(image_url):
    """Descarga una imagen desde URL y retorna los bytes"""
    try:
        response = requests.get(image_url)
        response.raise_for_status()
        return response.content
    except Exception as e:
        raise Exception(f"Error descargando imagen: {str(e)}")





def generate_single_image(image_bytes, prompt, image_type, frame_style):
    """
    Genera una imagen SIN reintentos.
    Si falla, retorna None inmediatamente.
    
    Args:
        image_bytes: Bytes de la imagen selfie (puede ser None)
        prompt: Prompt formateado para generar la imagen
        image_type: Tipo de imagen ('on_face' o 'product')
        frame_style: Estilo de la montura
    
    Returns:
        dict con la imagen generada o None si falla
    """
    try:
        # Preparar contenido según el tipo de imagen
        if image_type == 'on_face' and image_bytes:
            image_part = types.Part.from_bytes(
                data=image_bytes,
                mime_type="image/png"
            )
            contents = [prompt, image_part]
        else:
            contents = [prompt]
        
        # Configuración para respuesta multimodal
        config = types.GenerateContentConfig(
            response_modalities=["IMAGE"]
        )
        
        response = client.models.generate_content(
            model=IMAGE_MODEL,
            contents=contents,
            config=config
        )
        
        # Extraer tokens/uso de la respuesta
        usage_metadata = None
        if hasattr(response, 'usage_metadata'):
            usage_metadata = {
                "prompt_tokens": getattr(response.usage_metadata, 'prompt_token_count', 0),
                "output_tokens": getattr(response.usage_metadata, 'candidates_token_count', 0),
                "total_tokens": getattr(response.usage_metadata, 'total_token_count', 0)
            }
        
        # Extraer imagen
        if hasattr(response, 'candidates') and response.candidates:
            for candidate in response.candidates:
                if hasattr(candidate, 'content') and candidate.content:
                    for part in candidate.content.parts:
                        if hasattr(part, 'inline_data') and part.inline_data and part.inline_data.data:
                            img_data = base64.b64encode(part.inline_data.data).decode('utf-8')
                            return {
                                "data": f"data:{part.inline_data.mime_type};base64,{img_data}",
                                "mime_type": part.inline_data.mime_type,
                                "style": frame_style,
                                "type": image_type,
                                "usage": usage_metadata
                            }
        
        print(f"[WARN] No se generó imagen {image_type} para {frame_style}")
        return None
        
    except Exception as e:
        error_str = str(e)
        print(f"[ERROR] Error generando imagen {image_type} {frame_style}: {error_str}")
        return None


def generate_single_image_with_retry(image_bytes, prompt, image_type, frame_style, max_retries=3):
    """
    Genera una imagen CON reintentos automáticos y backoff exponencial.
    
    Maneja errores 429 (Rate Limiting) y 500 (Internal Error) reintentando
    automáticamente con esperas crecientes entre intentos.
    
    Args:
        image_bytes: Bytes de la imagen selfie (puede ser None)
        prompt: Prompt formateado para generar la imagen
        image_type: Tipo de imagen ('on_face' o 'product')
        frame_style: Estilo de la montura
        max_retries: Número máximo de intentos (default: 3)
    
    Returns:
        dict con la imagen generada o None si falla después de todos los intentos
    """
    import time
    
    # Backoff exponencial: 3s, 6s, 12s
    retry_delays = [3, 6, 12]
    
    for attempt in range(max_retries):
        # Intentar generar imagen
        result = generate_single_image(image_bytes, prompt, image_type, frame_style)
        
        if result:
            # Éxito
            if attempt > 0:
                print(f"[SUCCESS] ✓ Imagen {image_type} {frame_style} generada en intento {attempt + 1}/{max_retries}")
            return result
        
        # Si falló y quedan reintentos
        if attempt < max_retries - 1:
            wait_time = retry_delays[attempt]
            print(f"[RETRY] Reintentando {image_type} {frame_style} en {wait_time}s (intento {attempt + 2}/{max_retries})...")
            time.sleep(wait_time)
        else:
            # Último intento falló
            print(f"[ERROR] ✗ Falló {image_type} {frame_style} después de {max_retries} intentos")
    
    return None



def generate_glasses_images(selfie_url, user_data, on_image_generated=None):
    """
    Genera 4 imágenes: 2 monturas × (1 en rostro + 1 producto) = 4 imágenes total
    
    Args:
        selfie_url: URL de la selfie en Cloudinary
        user_data: Diccionario con datos del usuario (no usado)
        on_image_generated: Callback opcional que se llama cada vez que una imagen
                           es generada. Recibe (image_data, image_index) como parámetros.
                           Esto permite enviar imágenes progresivamente.
    
    Returns:
        dict: Resultado con imágenes generadas
    """
    import time
    
    DELAY_BETWEEN_CALLS = 4  # Segundos entre llamadas
    
    try:
        print(f"[DEBUG] Iniciando generación de imágenes con modelo: {IMAGE_MODEL}")
        
        # Descargar imagen selfie
        image_bytes = download_image_as_bytes(selfie_url)
        print(f"[DEBUG] Imagen descargada, tamaño: {len(image_bytes)} bytes")
        
        # Catálogo completo: 10 estilos de monturas
        # La IA analizará el rostro y elegirá los 2 MEJORES estilos de estos 10
        ALL_FRAME_STYLES = [
            {
                "id": "classic_rectangular",
                "name": "Rectangular Metálico",
                "style": "rectangular metal",
                "description": "Montura rectangular con armazón metálico, estilo profesional y elegante. Ideal para rostros redondos u ovalados."
            },
            {
                "id": "modern_round",
                "name": "Redondo de Acetato", 
                "style": "round acetate",
                "description": "Montura circular de acetato, estética retro-moderna. Perfecta para rostros cuadrados o angulares."
            },
            {
                "id": "aviator_metal",
                "name": "Aviador Metálico",
                "style": "aviator metal",
                "description": "Montura aviador clásica con puente doble y lentes en forma de lágrima invertida. Icónica y atemporal, favorece rostros cuadrados y rectangulares."
            },
            {
                "id": "cat_eye_acetate",
                "name": "Cat-Eye de Acetato",
                "style": "cat-eye acetate",
                "description": "Montura con esquinas superiores elevadas tipo ojo de gato. Femenina y vintage, ideal para rostros redondos, añade ángulos y sofisticación."
            },
            {
                "id": "wayfarer_acetate",
                "name": "Wayfarer de Acetato",
                "style": "wayfarer acetate",
                "description": "Montura trapezoidal clásica de acetato grueso. Versátil y urbana, favorece rostros ovalados, redondos y en forma de corazón."
            },
            {
                "id": "oversized_square",
                "name": "Cuadrado Oversized",
                "style": "oversized square acetate",
                "description": "Montura cuadrada de gran tamaño con armazón acetato. Moderna y statement, ideal para rostros pequeños o delicados que buscan impacto."
            },
            {
                "id": "browline_combo",
                "name": "Browline Combinado",
                "style": "browline combination",
                "description": "Montura con borde superior grueso (acetato/metal) y borde inferior delgado o sin marco. Retro-intelectual, favorece rostros ovalados y triangulares."
            },
            {
                "id": "geometric_angular",
                "name": "Geométrico Angular",
                "style": "geometric angular",
                "description": "Montura con formas octagonales o hexagonales. Vanguardista y artística, ideal para rostros redondos u ovalados que buscan contraste angular."
            },
            {
                "id": "semi_rimless",
                "name": "Semi-Rimless Minimalista",
                "style": "semi-rimless metal",
                "description": "Montura con marco solo en la parte superior, lentes sujetas por nylon transparente. Ligera y discreta, favorece cualquier rostro, especialmente profesionales."
            },
            {
                "id": "sport_wrap",
                "name": "Deportivo Wraparound",
                "style": "sport wraparound",
                "description": "Montura curva que envuelve el rostro, estilo deportivo moderno. Dinámico y juvenil, ideal para rostros angulares y activos."
            }
        ]
        
        # === SISTEMA DE CHECKPOINTS ===
        # Generar ID de sesión basado en la selfie URL
        session_id = get_session_id(selfie_url)
        print(f"[CHECKPOINT] Session ID: {session_id}")
        
        # Verificar estado de checkpoints existentes
        cache_status = get_session_status(session_id)
        cached_items = sum(1 for v in cache_status.values() if v)
        if cached_items > 0:
            print(f"[CHECKPOINT] Encontrados {cached_items} checkpoints anteriores")
        
        # PASO 1: Selección inteligente de estilos (con caché)
        print(f"[DEBUG] ========================================")
        print(f"[DEBUG] PASO 1: SELECCIÓN INTELIGENTE DE ESTILOS")
        print(f"[DEBUG] ========================================")
        
        # Verificar caché de estilos
        cached_styles = get_checkpoint(session_id, 'styles')
        if cached_styles:
            print(f"[CHECKPOINT] ✓ Usando estilos cacheados")
            frame_styles = cached_styles
        else:
            # Generar nueva selección
            frame_styles = select_best_frame_styles(image_bytes, ALL_FRAME_STYLES)
            # Guardar checkpoint
            save_checkpoint(session_id, 'styles', frame_styles)
        
        print(f"[DEBUG] Estilos seleccionados para esta persona:")
        for fs in frame_styles:
            print(f"[DEBUG]   - {fs['name']} ({fs['style']})")
        print(f"[DEBUG] ========================================")
        
        generated_images = []
        total_usage = {
            "prompt_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "image_generations": 0
        }
        
        # Generar imágenes SECUENCIALMENTE con diseño de especificaciones por adelantado
        for idx, frame in enumerate(frame_styles):
            print(f"[DEBUG] ========================================")
            print(f"[DEBUG] === Procesando montura {idx + 1}/2: {frame['name']} ===")
            print(f"[DEBUG] ========================================")
            
            # PASO 1: Diseñar especificaciones detalladas (con caché)
            specs_key = f"specs_{idx}"
            cached_specs = get_checkpoint(session_id, specs_key)
            
            if cached_specs:
                print(f"[CHECKPOINT] ✓ Usando especificaciones cacheadas para {frame['name']}")
                detailed_specs = cached_specs
            else:
                print(f"[DEBUG] PASO 1: Diseñando especificaciones detalladas para {frame['name']}...")
                detailed_specs = design_glasses_specifications(image_bytes, frame)
                save_checkpoint(session_id, specs_key, detailed_specs)
            
            print(f"[DEBUG] Especificaciones diseñadas: {detailed_specs}")
            
            # PASO 2: Generar imagen EN ROSTRO (con caché)
            on_face_key = f"img_on_face_{idx}"
            cached_on_face = get_checkpoint(session_id, on_face_key)
            
            if cached_on_face:
                print(f"[CHECKPOINT] ✓ Usando imagen en rostro cacheada para {frame['name']}")
                on_face_result = cached_on_face
            else:
                print(f"[DEBUG] PASO 2: Generando imagen en rostro con especificaciones exactas...")
                on_face_prompt = GLASSES_ON_FACE_PROMPT.format(detailed_specs=detailed_specs)
                
                on_face_result = generate_single_image_with_retry(
                    image_bytes=image_bytes,
                    prompt=on_face_prompt,
                    image_type='on_face',
                    frame_style=frame['id'],
                    max_retries=3
                )
                
                # Guardar checkpoint si exitoso
                if on_face_result:
                    on_face_result['frame_name'] = frame['name']
                    on_face_result['description'] = frame['description']
                    on_face_result['detailed_specs'] = detailed_specs
                    save_checkpoint(session_id, on_face_key, on_face_result)
            
            if on_face_result:
                generated_images.append(on_face_result)
                # Llamar callback para entrega progresiva
                if on_image_generated:
                    on_image_generated(on_face_result, len(generated_images) - 1)
                if on_face_result.get('usage'):
                    total_usage["prompt_tokens"] += on_face_result['usage'].get('prompt_tokens', 0)
                    total_usage["output_tokens"] += on_face_result['usage'].get('output_tokens', 0)
                    total_usage["total_tokens"] += on_face_result['usage'].get('total_tokens', 0)
                total_usage["image_generations"] += 1
                print(f"[DEBUG] ✓ Imagen en rostro generada: {frame['name']}")
            else:
                print(f"[WARN] ✗ Falló imagen en rostro: {frame['name']}")
            
            # Delay entre imágenes
            print(f"[DEBUG] Esperando {DELAY_BETWEEN_CALLS}s...")
            time.sleep(DELAY_BETWEEN_CALLS)
            
            # PASO 3: Generar imagen de PRODUCTO (con caché)
            product_key = f"img_product_{idx}"
            cached_product = get_checkpoint(session_id, product_key)
            
            if cached_product:
                print(f"[CHECKPOINT] ✓ Usando imagen de producto cacheada para {frame['name']}")
                product_result = cached_product
            else:
                print(f"[DEBUG] PASO 3: Generando imagen de producto con MISMAS especificaciones (mismo color)...")
                product_prompt = GLASSES_PRODUCT_PROMPT.format(detailed_specs=detailed_specs)
                
                product_result = generate_single_image_with_retry(
                    image_bytes=None,  # No necesita la selfie
                    prompt=product_prompt,
                    image_type='product',
                    frame_style=frame['id'],
                    max_retries=3
                )
                
                # Guardar checkpoint si exitoso
                if product_result:
                    product_result['frame_name'] = frame['name']
                    product_result['description'] = frame['description']
                    product_result['detailed_specs'] = detailed_specs
                    save_checkpoint(session_id, product_key, product_result)
            
            if product_result:
                generated_images.append(product_result)
                # Llamar callback para entrega progresiva
                if on_image_generated:
                    on_image_generated(product_result, len(generated_images) - 1)
                if product_result.get('usage'):
                    total_usage["prompt_tokens"] += product_result['usage'].get('prompt_tokens', 0)
                    total_usage["output_tokens"] += product_result['usage'].get('output_tokens', 0)
                    total_usage["total_tokens"] += product_result['usage'].get('total_tokens', 0)
                total_usage["image_generations"] += 1
                print(f"[DEBUG] ✓ Imagen de producto generada: {frame['name']}")
            else:
                print(f"[WARN] ✗ Falló imagen de producto: {frame['name']}")
            
            # Delay antes de siguiente montura (si no es la última)
            if idx < len(frame_styles) - 1:
                print(f"[DEBUG] Esperando {DELAY_BETWEEN_CALLS}s antes de siguiente montura...")
                time.sleep(DELAY_BETWEEN_CALLS)
        
        final_count = len(generated_images)
        on_face_count = sum(1 for img in generated_images if img.get('type') == 'on_face')
        product_count = sum(1 for img in generated_images if img.get('type') == 'product')
        
        print(f"[DEBUG] ========================================")
        print(f"[DEBUG] RESULTADO FINAL DE GENERACIÓN:")
        print(f"[DEBUG] - Total imágenes: {final_count}/4")
        print(f"[DEBUG] - En rostro: {on_face_count}/2")
        print(f"[DEBUG] - Producto: {product_count}/2")
        print(f"[DEBUG] ========================================")
        
        # Validar que se generaron exactamente 4 imágenes
        if final_count == 4:
            success_msg = "✓ Se generaron exitosamente las 4 imágenes requeridas"
            print(f"[SUCCESS] {success_msg}")
            # Limpiar caché después de éxito completo
            clear_session(session_id)
            print(f"[CHECKPOINT] Caché limpiado después de éxito")
            error = None
        elif final_count > 0:
            warning_msg = f"Se generaron solo {final_count}/4 imágenes ({on_face_count} en rostro, {product_count} producto)"
            print(f"[WARN] {warning_msg}")
            error = warning_msg
        else:
            error = "No se pudo generar ninguna imagen"
        
        return {
            "success": final_count >= 4,  # Éxito SOLO si se generaron las 4 imágenes
            "images": generated_images,
            "count": final_count,
            "on_face_count": on_face_count,
            "product_count": product_count,
            "usage": total_usage,
            "error": error
        }
        
    except Exception as e:
        import traceback
        error_msg = str(e)
        print(f"[ERROR] Error generando imágenes: {error_msg}")
        print(f"[ERROR] Traceback: {traceback.format_exc()}")
        return {
            "success": False,
            "error": error_msg,
            "images": generated_images if 'generated_images' in locals() else [],
            "usage": total_usage if 'total_usage' in locals() else None
        }


def generate_text_analysis(selfie_url, user_data):
    """
    Genera análisis en texto de las recomendaciones de monturas
    
    Args:
        selfie_url: URL de la selfie en Cloudinary
        user_data: Diccionario con datos del usuario
    
    Returns:
        dict: Resultado con análisis en texto, tokens usados, o error
    """
    try:
        print(f"[DEBUG] Iniciando análisis de texto con modelo: {TEXT_MODEL}")
        
        # Descargar imagen selfie
        image_bytes = download_image_as_bytes(selfie_url)
        
        # Usar el prompt directamente (ya no requiere datos del usuario)
        prompt = TEXT_ANALYSIS_PROMPT
        
        # Crear contenido con imagen
        image_part = types.Part.from_bytes(
            data=image_bytes,
            mime_type="image/png"
        )
        
        # Generar respuesta (solo texto)
        response = client.models.generate_content(
            model=TEXT_MODEL,
            contents=[prompt, image_part]
        )
        
        # Extraer tokens/uso de la respuesta
        usage_metadata = None
        if hasattr(response, 'usage_metadata'):
            usage_metadata = {
                "prompt_tokens": getattr(response.usage_metadata, 'prompt_token_count', 0),
                "output_tokens": getattr(response.usage_metadata, 'candidates_token_count', 0),
                "total_tokens": getattr(response.usage_metadata, 'total_token_count', 0)
            }
            print(f"[DEBUG] Tokens de análisis de texto: {usage_metadata}")
        
        # Extraer texto de la respuesta
        text_response = ""
        if hasattr(response, 'text'):
            text_response = response.text
        elif hasattr(response, 'candidates') and response.candidates:
            for candidate in response.candidates:
                if hasattr(candidate, 'content') and candidate.content:
                    for part in candidate.content.parts:
                        if hasattr(part, 'text') and part.text:
                            text_response += part.text
        
        print(f"[DEBUG] Análisis de texto completado, longitud: {len(text_response)} chars")
        
        return {
            "success": True,
            "analysis": text_response,
            "usage": usage_metadata
        }
        
    except Exception as e:
        import traceback
        error_msg = str(e)
        print(f"[ERROR] Error generando análisis de texto: {error_msg}")
        print(f"[ERROR] Traceback: {traceback.format_exc()}")
        return {
            "success": False,
            "error": error_msg,
            "usage": None
        }

def analyze_face_for_glasses(selfie_url, user_data, tracker=None):
    """
    Función principal que combina generación de imágenes y análisis de texto.
    OPTIMIZADO: Ejecuta primero el texto (más rápido) y luego las imágenes.
    
    Args:
        selfie_url: URL de la selfie en Cloudinary
        user_data: Diccionario con datos del usuario
        tracker: ProgressTracker opcional para reportar progreso
    
    Returns:
        dict: Resultado completo con imágenes, análisis y costos
    """
    import time
    
    start_time = time.time()
    print("[PERF] Iniciando análisis...")
    
    if tracker:
        tracker.update(5, "Iniciando análisis con IA...")
    
    images_result = {"success": False, "images": [], "error": None, "usage": None}
    text_result = {"success": False, "analysis": "", "error": None, "usage": None}
    
    try:
        # === PASO 1: ANÁLISIS DE TEXTO (más rápido, ~20-50s) ===
        if tracker:
            tracker.update(10, "Analizando tu rostro...")
        
        print("[DEBUG] Paso 1/2: Generando análisis de texto...")
        text_result = generate_text_analysis(selfie_url, user_data)
        
        text_time = time.time() - start_time
        print(f"[PERF] Texto completado en {text_time:.2f}s")
        
        if tracker:
            tracker.update(40, "Análisis facial completado ✓ Generando monturas...")
        
        # === PASO 2: GENERAR IMÁGENES (más lento, ~30-90s) ===
        print("[DEBUG] Paso 2/2: Generando imágenes de monturas...")
        images_result = generate_glasses_images(selfie_url, user_data)
        
        images_time = time.time() - start_time
        print(f"[PERF] Imágenes completadas en {images_time:.2f}s")
        
        if tracker:
            tracker.update(95, "Preparando resultados...")
        
    except Exception as e:
        import traceback
        print(f"[ERROR] Error en análisis principal: {str(e)}")
        print(f"[ERROR] Traceback: {traceback.format_exc()}")
    
    total_time = time.time() - start_time
    print(f"[PERF] Análisis total completado en {total_time:.2f}s")
    
    # Calcular costos totales combinados
    total_usage = {
        "prompt_tokens": 0,
        "output_tokens": 0,
        "total_tokens": 0,
        "image_generations": 0,
        "text_generations": 0,
        "processing_time_seconds": round(total_time, 2)
    }
    
    # Agregar tokens de imágenes
    if images_result and images_result.get("usage"):
        img_usage = images_result["usage"]
        total_usage["prompt_tokens"] += img_usage.get("prompt_tokens", 0)
        total_usage["output_tokens"] += img_usage.get("output_tokens", 0)
        total_usage["total_tokens"] += img_usage.get("total_tokens", 0)
        total_usage["image_generations"] = img_usage.get("image_generations", 0)
    
    # Agregar tokens de texto
    if text_result and text_result.get("usage"):
        txt_usage = text_result["usage"]
        total_usage["prompt_tokens"] += txt_usage.get("prompt_tokens", 0)
        total_usage["output_tokens"] += txt_usage.get("output_tokens", 0)
        total_usage["total_tokens"] += txt_usage.get("total_tokens", 0)
        total_usage["text_generations"] = 1
    
    print(f"[DEBUG] Uso total de tokens: {total_usage}")
    
    # Marcar como completado SIEMPRE (para evitar que se quede en 90%)
    if tracker:
        tracker.complete()
    
    # Si ambos fallaron
    if not text_result.get("success") and not images_result.get("success"):
        return {
            "success": False,
            "error": f"Imágenes: {images_result.get('error')} | Texto: {text_result.get('error')}",
            "images": [],
            "analysis": "",
            "usage": total_usage
        }
    
    # Retornar resultados (incluso si uno de los dos falló)
    return {
        "success": True,
        "images": images_result.get("images", []),
        "analysis": text_result.get("analysis", ""),
        "images_error": images_result.get("error"),
        "text_error": text_result.get("error"),
        "usage": total_usage
    }

