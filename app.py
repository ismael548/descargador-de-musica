from flask import Flask, render_template, request, send_file, jsonify
import requests
import os
import time

app = Flask(__name__)

DOWNLOAD_FOLDER = "downloads"
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)


def descargar_con_cobalt(url):
    """
    Usa la API de Cobalt v10 para descargar de YouTube
    """
    # API de Cobalt v10
    api_url = "https://api.cobalt.tools/api/download"
    
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    
    data = {
        "url": url,
        "downloadMode": "audio",
        "audioFormat": "mp3",
        "filenameStyle": "basic",
    }
    
    # Primera petición: pedir la descarga
    response = requests.post(api_url, headers=headers, json=data, timeout=30)
    result = response.json()
    
    if result.get("status") == "stream" or result.get("status") == "redirect":
        # Obtener el link directo del audio
        audio_url = result.get("url")
        
        # Descargar el archivo
        audio_response = requests.get(audio_url, timeout=120)
        
        # Guardar con nombre único
        timestamp = int(time.time())
        filename = f"cancion_{timestamp}.mp3"
        filepath = os.path.join(DOWNLOAD_FOLDER, filename)
        
        with open(filepath, "wb") as f:
            f.write(audio_response.content)
        
        return filename
    
    elif result.get("status") == "error" or result.get("status") == "picker":
        raise Exception(result.get("text", "Error desconocido de Cobalt"))
    
    else:
        raise Exception(f"Respuesta inesperada: {result}")


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/descargar', methods=['POST'])
def descargar():
    url = request.form.get('url')
    
    if not url:
        return jsonify({'error': 'No se proporcionó URL'}), 400
    
    try:
        filename = descargar_con_cobalt(url)
        
        return jsonify({
            'success': True,
            'mensaje': '¡Descarga completada!',
            'archivo': filename
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/descargar_archivo/<nombre>')
def descargar_archivo(nombre):
    ruta = os.path.join(DOWNLOAD_FOLDER, nombre)
    return send_file(ruta, as_attachment=True)


if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
