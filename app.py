from flask import Flask, render_template, request, send_file, jsonify
import requests
import os
import time
import re
import traceback
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

DOWNLOAD_FOLDER = "downloads"
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

# ========== CONFIGURA TU API KEY AQUÍ ==========
# Mejor usar variable de entorno para seguridad
RAPIDAPI_KEY = os.environ.get("RAPIDAPI_KEY", "05792df5e0mshfc80c13c6697756p126763jsn45de2ded29ca")
RAPIDAPI_HOST = "youtube-mp3-audio-video-downloader.p.rapidapi.com"
BASE_URL = f"https://{RAPIDAPI_HOST}"

HEADERS = {
    "X-RapidAPI-Key": RAPIDAPI_KEY,
    "X-RapidAPI-Host": RAPIDAPI_HOST,
    "Content-Type": "application/json"
}


# ========== MANEJADORES DE ERROR GLOBALES ==========

@app.errorhandler(404)
def not_found(error):
    logger.error(f"404 Error: {request.path}")
    if request.path.startswith('/descargar') or request.path.startswith('/buscar') or request.path.startswith('/info'):
        return jsonify({'error': 'Endpoint no encontrado', 'path': request.path}), 404
    return render_template('index.html')

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"500 Error: {str(error)}\n{traceback.format_exc()}")
    return jsonify({'error': 'Error interno del servidor', 'detail': str(error)}), 500

@app.errorhandler(Exception)
def handle_exception(error):
    logger.error(f"Unhandled Exception: {str(error)}\n{traceback.format_exc()}")
    # Si es una petición AJAX/API, devolver JSON
    if request.is_json or request.headers.get('Accept') == 'application/json':
        return jsonify({'error': 'Error inesperado', 'detail': str(error)}), 500
    return jsonify({'error': 'Error inesperado', 'detail': str(error)}), 500


# ========== FUNCIONES AUXILIARES ==========

def extraer_video_id(url):
    """Extrae el video ID de cualquier URL de YouTube"""
    if not url:
        return None

    patterns = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/|youtube\.com/v/|youtube\.com/shorts/)([a-zA-Z0-9_-]{11})',
        r'[?&]v=([a-zA-Z0-9_-]{11})',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def safe_api_request(method, url, **kwargs):
    """Hace una petición a la API con manejo de errores"""
    try:
        logger.info(f"API Request: {method} {url}")
        response = requests.request(method, url, timeout=60, **kwargs)
        logger.info(f"API Response: {response.status_code} - Content-Type: {response.headers.get('Content-Type', 'unknown')}")

        # Verificar que la respuesta sea JSON
        content_type = response.headers.get('Content-Type', '')
        if 'application/json' not in content_type:
            logger.warning(f"Respuesta no es JSON. Content-Type: {content_type}")
            logger.warning(f"Primeros 200 chars: {response.text[:200]}")

            # Si es HTML, probablemente sea error del servidor
            if '<html' in response.text.lower() or '<!doctype' in response.text.lower():
                raise Exception(f"La API devolvió HTML en lugar de JSON (status {response.status_code}). Posible error del servidor de RapidAPI.")

            raise Exception(f"Respuesta inesperada de la API: {content_type}")

        if response.status_code != 200:
            try:
                error_data = response.json()
                raise Exception(f"Error API {response.status_code}: {error_data}")
            except:
                raise Exception(f"Error API {response.status_code}: {response.text[:200]}")

        return response.json()

    except requests.exceptions.Timeout:
        raise Exception("La API tardó demasiado en responder. Intenta de nuevo.")
    except requests.exceptions.ConnectionError:
        raise Exception("Error de conexión con la API. Verifica tu conexión a internet.")
    except Exception as e:
        raise Exception(f"Error en petición API: {str(e)}")


def obtener_info_video(video_id):
    """Obtiene información del video"""
    url = f"{BASE_URL}/get-video-info/{video_id}"
    params = {"response_mode": "default"}
    return safe_api_request("GET", url, headers=HEADERS, params=params)


def obtener_url_descarga_m4a(video_id, lang=None):
    """Obtiene link directo M4A"""
    url = f"{BASE_URL}/get_m4a_download_link/{video_id}"
    params = {}
    if lang:
        params["lang"] = lang
    data = safe_api_request("GET", url, headers=HEADERS, params=params)
    return data.get("file") or data.get("reserved_file")


def obtener_url_descarga_mp3(video_id, quality="low", wait_ready=True, lang=None):
    """Obtiene link directo MP3"""
    url = f"{BASE_URL}/get_mp3_download_link/{video_id}"
    params = {
        "quality": quality,
        "wait_until_the_file_is_ready": "true" if wait_ready else "false"
    }
    if lang:
        params["lang"] = lang
    data = safe_api_request("GET", url, headers=HEADERS, params=params)
    return data.get("file") or data.get("reserved_file")


def descargar_archivo(download_url, filename):
    """Descarga el archivo desde el link directo"""
    max_attempts = 20
    wait_seconds = 5

    for attempt in range(1, max_attempts + 1):
        logger.info(f"Descarga intento {attempt}/{max_attempts}")

        try:
            file_response = requests.get(download_url, timeout=120, allow_redirects=True)
            content_length = len(file_response.content)
            content_type = file_response.headers.get('Content-Type', '')

            logger.info(f"Respuesta descarga: Status={file_response.status_code}, Size={content_length}, Type={content_type}")

            # Verificar que sea un archivo de audio válido
            first_bytes = file_response.content[:100]
            is_html = b'<html' in first_bytes.lower() or b'<!doctype' in first_bytes.lower()

            if file_response.status_code == 200 and content_length > 5000 and not is_html:
                filepath = os.path.join(DOWNLOAD_FOLDER, filename)
                with open(filepath, "wb") as f:
                    f.write(file_response.content)
                logger.info(f"Archivo guardado: {filename} ({content_length} bytes)")
                return filepath

            if is_html:
                logger.warning("Recibido HTML en lugar de audio")

            logger.info(f"Archivo aún no listo, esperando {wait_seconds}s...")
            time.sleep(wait_seconds)

        except Exception as e:
            logger.error(f"Error en descarga intento {attempt}: {e}")
            time.sleep(wait_seconds)

    raise Exception("El archivo no estuvo listo después de varios intentos. La conversión puede tardar 20-300 segundos según la API.")


def buscar_videos(query, limit=10):
    """Busca videos en YouTube"""
    url = f"{BASE_URL}/search_video"
    params = {
        "query": query,
        "limit": limit,
        "sort_by": "relevance",
        "response_mode": "default"
    }
    return safe_api_request("GET", url, headers=HEADERS, params=params)


# ========== RUTAS ==========

@app.route('/ping')
def ping():
    """Endpoint para mantener la app despierta en Render free tier"""
    return jsonify({'status': 'ok', 'time': time.time()})


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/info', methods=['POST'])
def info_video():
    url = request.form.get('url') or request.json.get('url') if request.is_json else None

    if not url:
        return jsonify({'error': 'No se proporcionó URL'}), 400

    video_id = extraer_video_id(url)
    if not video_id:
        return jsonify({'error': 'URL de YouTube no válida'}), 400

    try:
        info = obtener_info_video(video_id)
        return jsonify({'success': True, 'video_id': video_id, 'info': info})
    except Exception as e:
        logger.error(f"Error en info_video: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/descargar', methods=['POST'])
def descargar():
    url = request.form.get('url')
    formato = request.form.get('formato', 'mp3')
    calidad = request.form.get('calidad', 'low')

    logger.info(f"Solicitud de descarga: url={url}, formato={formato}, calidad={calidad}")

    if not url:
        return jsonify({'error': 'No se proporcionó URL'}), 400

    video_id = extraer_video_id(url)
    if not video_id:
        return jsonify({'error': 'URL de YouTube no válida. Usa youtube.com/watch?v=... o youtu.be/...'}), 400

    try:
        # Obtener info para el nombre del archivo
        try:
            info = obtener_info_video(video_id)
            titulo = info.get('title', f'audio_{video_id}')
            titulo_limpio = re.sub(r'[<>\\/|?*:"]', '', titulo)[:50]
        except Exception as e:
            logger.warning(f"No se pudo obtener info del video: {e}")
            titulo_limpio = f"audio_{video_id}"

        # Obtener link de descarga
        if formato.lower() == 'm4a':
            download_url = obtener_url_descarga_m4a(video_id)
            extension = "m4a"
        else:
            download_url = obtener_url_descarga_mp3(video_id, quality=calidad, wait_ready=True)
            extension = "mp3"

        if not download_url:
            return jsonify({'error': 'La API no devolvió link de descarga'}), 500

        logger.info(f"Link de descarga obtenido: {download_url[:80]}...")

        # Descargar archivo
        timestamp = int(time.time())
        filename = f"{titulo_limpio}_{timestamp}.{extension}"
        filepath = descargar_archivo(download_url, filename)

        return jsonify({
            'success': True,
            'mensaje': f'¡Descarga completada en formato {extension.upper()}!',
            'archivo': filename,
            'titulo': titulo_limpio,
            'formato': extension,
            'download_url': f'/descargar_archivo/{filename}'
        })

    except Exception as e:
        logger.error(f"Error en descargar: {e}\n{traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500


@app.route('/buscar', methods=['POST'])
def buscar():
    query = request.form.get('query') or (request.json.get('query') if request.is_json else None)

    if not query:
        return jsonify({'error': 'No se proporcionó término de búsqueda'}), 400

    try:
        resultados = buscar_videos(query)
        return jsonify({'success': True, 'resultados': resultados})
    except Exception as e:
        logger.error(f"Error en buscar: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/descargar_archivo/<nombre>')
def descargar_archivo_route(nombre):
    ruta = os.path.join(DOWNLOAD_FOLDER, nombre)
    if not os.path.exists(ruta):
        return jsonify({'error': 'Archivo no encontrado'}), 404
    return send_file(ruta, as_attachment=True)


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    logger.info(f"Iniciando servidor en puerto {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
