from flask import Flask, render_template, request, send_file, jsonify
import yt_dlp
import os

app = Flask(__name__)

# Carpeta donde se guardan las descargas
DOWNLOAD_FOLDER = "downloads"
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)


def descargar_audio(url):
    """
    Descarga el audio y devuelve el nombre del archivo.
    """
    opciones = {
        'format': 'bestaudio/best',
        'outtmpl': f'{DOWNLOAD_FOLDER}/%(title)s.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'extractor_args': {'youtube': {'player_client': ['android']}},
    }
    
    with yt_dlp.YoutubeDL(opciones) as ydl:
        info = ydl.extract_info(url, download=True)
        titulo = info.get('title', 'cancion')
    
    # Buscar el archivo MP3 generado
    for archivo in os.listdir(DOWNLOAD_FOLDER):
        if archivo.endswith('.mp3') and titulo in archivo:
            return archivo
    
    return None


@app.route('/')
def home():
    """Muestra la página principal"""
    return render_template('index.html')


@app.route('/descargar', methods=['POST'])
def descargar():
    """Recibe la URL y descarga la música"""
    url = request.form.get('url')
    
    if not url:
        return jsonify({'error': 'No se proporcionó URL'}), 400
    
    try:
        nombre_archivo = descargar_audio(url)
        
        if nombre_archivo:
            return jsonify({
                'success': True,
                'mensaje': '¡Descarga completada!',
                'archivo': nombre_archivo
            })
        else:
            return jsonify({'error': 'No se pudo descargar'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/descargar_archivo/<nombre>')
def descargar_archivo(nombre):
    """Permite descargar el archivo MP3"""
    ruta = os.path.join(DOWNLOAD_FOLDER, nombre)
    return send_file(ruta, as_attachment=True)


if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
