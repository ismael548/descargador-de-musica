from flask import Flask, render_template, request, send_file, jsonify, redirect, url_for
import requests
import os
import time
import re

app = Flask(__name__)

DOWNLOAD_FOLDER = "downloads"
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

# ========== CONFIGURA TU API KEY AQUÍ ==========
RAPIDAPI_KEY = "05792df5e0mshfc80c13c6697756p126763jsn45de2ded29ca"
RAPIDAPI_HOST = "youtube-mp3-audio-video-downloader.p.rapidapi.com"
BASE_URL = f"https://{RAPIDAPI_HOST}"

HEADERS = {
    "X-RapidAPI-Key": RAPIDAPI_KEY,
    "X-RapidAPI-Host": RAPIDAPI_HOST,
    "Content-Type": "application/json"
}


def extraer_video_id(url):
    """Extrae el video ID de cualquier URL de YouTube"""
    patterns = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/|youtube\.com/v/)([a-zA-Z0-9_-]{11})',
        r'youtube\.com/shorts/([a-zA-Z0-9_-]{11})',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def obtener_info_video(video_id):
    """Obtiene información del video usando el endpoint Get Video Information"""
    url = f"{BASE_URL}/get-video-info/{video_id}"
    params = {"response_mode": "default"}

    response = requests.get(url, headers=HEADERS, params=params, timeout=30)

    if response.status_code != 200:
        raise Exception(f"Error al obtener información del video: {response.status_code}")

    return response.json()


def obtener_url_descarga_m4a(video_id, lang=None):
    """Obtiene el link directo de descarga en formato M4A"""
    url = f"{BASE_URL}/get_m4a_download_link/{video_id}"
    params = {}
    if lang:
        params["lang"] = lang

    response = requests.get(url, headers=HEADERS, params=params, timeout=30)

    if response.status_code != 200:
        raise Exception(f"Error al obtener link M4A: {response.status_code}")

    data = response.json()
    return data.get("file") or data.get("reserved_file") or data.get("downloadUrl")


def obtener_url_descarga_mp3(video_id, quality="low", wait_ready=True, lang=None):
    """Obtiene el link directo de descarga en formato MP3"""
    url = f"{BASE_URL}/get_mp3_download_link/{video_id}"
    params = {
        "quality": quality,
        "wait_until_the_file_is_ready": "true" if wait_ready else "false"
    }
    if lang:
        params["lang"] = lang

    response = requests.get(url, headers=HEADERS, params=params, timeout=60)

    if response.status_code != 200:
        raise Exception(f"Error al obtener link MP3: {response.status_code}")

    data = response.json()
    return data.get("file") or data.get("reserved_file") or data.get("downloadUrl")


def descargar_archivo(download_url, filename):
    """Descarga el archivo desde el link directo y lo guarda localmente"""
    max_attempts = 15
    wait_seconds = 3

    for attempt in range(1, max_attempts + 1):
        print(f"⏳ Intento {attempt}/{max_attempts} - Descargando archivo...")

        file_response = requests.get(download_url, timeout=120, allow_redirects=True)

        # Verificar que sea un archivo válido (no HTML de error)
        content_type = file_response.headers.get('Content-Type', '')
        content_length = len(file_response.content)

        print(f"   Status: {file_response.status_code} | Type: {content_type} | Size: {content_length} bytes")

        if file_response.status_code == 200 and content_length > 5000:
            # Verificar que no sea HTML de error
            if b'<html' in file_response.content[:100].lower() or b'<!doctype' in file_response.content[:100].lower():
                print(f"   ⚠️ Recibido HTML en lugar de audio, reintentando...")
                time.sleep(wait_seconds)
                continue

            filepath = os.path.join(DOWNLOAD_FOLDER, filename)
            with open(filepath, "wb") as f:
                f.write(file_response.content)

            print(f"✅ Archivo guardado: {filename} ({content_length} bytes)")
            return filepath

        print(f"   ⚠️ Archivo aún no listo, esperando {wait_seconds}s...")
        time.sleep(wait_seconds)

    raise Exception("El archivo no estuvo listo después de varios intentos. La API indica que puede tardar 20-300 segundos.")


def buscar_videos(query, limit=10):
    """Busca videos en YouTube usando la API"""
    url = f"{BASE_URL}/search_video"
    params = {
        "query": query,
        "limit": limit,
        "sort_by": "relevance",
        "response_mode": "default"
    }

    response = requests.get(url, headers=HEADERS, params=params, timeout=30)

    if response.status_code != 200:
        raise Exception(f"Error en búsqueda: {response.status_code}")

    return response.json()


# ========== RUTAS DE LA APP ==========

@app.route('/')
def home():
    return render_template('index.html')


@app.route('/info', methods=['POST'])
def info_video():
    """Obtiene información de un video de YouTube"""
    url = request.json.get('url') or request.form.get('url')

    if not url:
        return jsonify({'error': 'No se proporcionó URL'}), 400

    video_id = extraer_video_id(url)
    if not video_id:
        return jsonify({'error': 'URL de YouTube no válida'}), 400

    try:
        info = obtener_info_video(video_id)
        return jsonify({
            'success': True,
            'video_id': video_id,
            'info': info
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/descargar', methods=['POST'])
def descargar():
    """Descarga el audio de un video de YouTube"""
    url = request.form.get('url') or request.json.get('url')
    formato = request.form.get('formato', 'mp3')  # mp3 o m4a
    calidad = request.form.get('calidad', 'low')   # low, medium, high

    if not url:
        return jsonify({'error': 'No se proporcionó URL'}), 400

    video_id = extraer_video_id(url)
    if not video_id:
        return jsonify({'error': 'URL de YouTube no válida. Formatos soportados: youtube.com/watch?v=... o youtu.be/...'}), 400

    try:
        # Obtener información del video para ponerle buen nombre
        try:
            info = obtener_info_video(video_id)
            titulo = info.get('title', f'audio_{video_id}')
            # Limpiar caracteres inválidos para nombre de archivo
            titulo_limpio = re.sub(r'[<>\/|?*:":]', '', titulo)[:50]
        except:
            titulo_limpio = f"audio_{video_id}"

        # Obtener link de descarga según formato
        if formato.lower() == 'm4a':
            download_url = obtener_url_descarga_m4a(video_id)
            extension = "m4a"
        else:
            download_url = obtener_url_descarga_mp3(video_id, quality=calidad, wait_ready=True)
            extension = "mp3"

        if not download_url:
            return jsonify({'error': 'No se pudo obtener el link de descarga de la API'}), 500

        # Descargar el archivo
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
        print(f"❌ Error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/buscar', methods=['POST'])
def buscar():
    """Busca videos en YouTube"""
    query = request.form.get('query') or request.json.get('query')

    if not query:
        return jsonify({'error': 'No se proporcionó término de búsqueda'}), 400

    try:
        resultados = buscar_videos(query)
        return jsonify({
            'success': True,
            'resultados': resultados
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/descargar_archivo/<nombre>')
def descargar_archivo(nombre):
    """Sirve el archivo descargado para que el usuario lo baje"""
    ruta = os.path.join(DOWNLOAD_FOLDER, nombre)
    if not os.path.exists(ruta):
        return jsonify({'error': 'Archivo no encontrado'}), 404
    return send_file(ruta, as_attachment=True)


@app.route('/stream/<nombre>')
def stream_audio(nombre):
    """Reproduce el audio sin descargar"""
    ruta = os.path.join(DOWNLOAD_FOLDER, nombre)
    if not os.path.exists(ruta):
        return jsonify({'error': 'Archivo no encontrado'}), 404
    return send_file(ruta)


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
