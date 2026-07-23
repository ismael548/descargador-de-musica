import os
import re
import time
from flask import Flask, render_template, request, jsonify, send_from_directory
import yt_dlp

app = Flask(__name__)

# Configurar directorio de descargas temporales
DOWNLOAD_FOLDER = os.path.join(app.root_path, 'downloads')
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# Función para limpiar archivos viejos (> 10 minutos) para evitar llenar el disco de Render
def limpiar_descargas_antiguas():
    ahora = time.time()
    for archivo in os.listdir(DOWNLOAD_FOLDER):
        ruta = os.path.join(DOWNLOAD_FOLDER, archivo)
        if os.path.isfile(ruta):
            # Si el archivo tiene más de 10 minutos, se borra
            if ahora - os.path.getmtime(ruta) > 600:
                try:
                    os.remove(ruta)
                except Exception:
                    pass

@app.route('/')
def index():
    return render_template('index.html')

# RUTA DE DIAGNÓSTICO PARA VERIFICAR COOKIES
@app.route('/test_cookies')
def test_cookies():
    cookies_path = os.path.join(app.root_path, 'cookies.txt')
    exists = os.path.exists(cookies_path)
    if not exists:
        return jsonify({
            'success': False, 
            'message': 'cookies.txt no existe en el servidor',
            'root_path': app.root_path,
            'files_in_root': os.listdir(app.root_path)
        }), 404
    
    try:
        size = os.path.getsize(cookies_path)
        with open(cookies_path, 'r', encoding='utf-8', errors='ignore') as f:
            head = f.read(200)
        return jsonify({
            'success': True,
            'size_bytes': size,
            'first_200_chars': head,
            'root_path': app.root_path,
            'files_in_root': os.listdir(app.root_path)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/descargar')
def download():
    # Limpiamos archivos temporales viejos
    limpiar_descargas_antiguas()

    video_url = request.args.get('url')
    if not video_url:
        return jsonify({'success': False, 'error': 'Falta la URL de la canción'}), 400

    try:
        # Validación y extracción del ID del video
        patron = r'(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/|youtube\.com\/shorts\/)([a-zA-Z0-9_-]{11})'
        resultado = re.search(patron, video_url)
        
        if not resultado:
            return jsonify({'success': False, 'error': 'Por favor, ingresa un enlace válido de YouTube'}), 400
            
        video_id = resultado.group(1)
        url_limpia = f"https://www.youtube.com/watch?v={video_id}"

        # Ruta a cookies.txt para evitar bloqueos por parte de YouTube
        cookies_path = os.path.join(app.root_path, 'cookies.txt')

        # Configuración de yt-dlp
        ydl_opts = {
            'format': 'bestaudio/best',
            # Nombre temporal del archivo de salida
            'outtmpl': os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True,
            'no_warnings': True,
        }

        # Si el archivo cookies.txt existe, lo usamos
        if os.path.exists(cookies_path):
            ydl_opts['cookiefile'] = cookies_path

        # Descargar el video y extraer metadatos
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url_limpia, download=True)
            filename_original = ydl.prepare_filename(info)
            # Reemplazar la extensión original por .mp3 debido al postprocessor
            filename_mp3 = os.path.splitext(filename_original)[0] + '.mp3'
            
            basename_mp3 = os.path.basename(filename_mp3)
            titulo = info.get('title', 'musica_descargada')

        return jsonify({
            'success': True,
            'download_url': f"/guardar/{basename_mp3}",
            'title': titulo
        })

    except Exception as e:
        return jsonify({'success': False, 'error': f"Error en la descarga/conversión: {str(e)}"}), 500

@app.route('/guardar/<path:filename>')
def guardar_archivo(filename):
    # Sirve el archivo descargado desde el almacenamiento temporal
    return send_from_directory(DOWNLOAD_FOLDER, filename, as_attachment=True)

if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
