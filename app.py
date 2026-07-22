from flask import Flask, render_template, request, send_file, jsonify
import requests
import os
import time

app = Flask(__name__)

DOWNLOAD_FOLDER = "downloads"
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

# Tu API Key de RapidAPI (la pegas aquí)
RAPIDAPI_KEY = "TU_API_KEY_AQUI"
RAPIDAPI_HOST = "youtube-mp3-download1.p.rapidapi.com"  # Esto puede variar según la API


def descargar_con_api(url):
    """
    Usa RapidAPI para descargar MP3 de YouTube
    """
    
    # Extraer video ID del URL
    video_id = None
    if "youtu.be/" in url:
        video_id = url.split("youtu.be/")[1].split("?")[0]
    elif "v=" in url:
        video_id = url.split("v=")[1].split("&")[0]
    
    if not video_id:
        raise Exception("URL de YouTube no válida")
    
    # Llamar a la API
    api_url = f"https://{RAPIDAPI_HOST}/v1"
    
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": RAPIDAPI_HOST,
    }
    
    querystring = {"videoId": video_id}
    
    response = requests.get(api_url, headers=headers, params=querystring, timeout=30)
    result = response.json()
    
    if "link" in result:
        # Descargar el MP3
        mp3_url = result["link"]
        mp3_response = requests.get(mp3_url, timeout=120)
        
        # Guardar
        timestamp = int(time.time())
        filename = f"cancion_{timestamp}.mp3"
        filepath = os.path.join(DOWNLOAD_FOLDER, filename)
        
        with open(filepath, "wb") as f:
            f.write(mp3_response.content)
        
        return filename
    else:
        raise Exception(f"Error de API: {result.get('msg', 'Desconocido')}")


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/descargar', methods=['POST'])
def descargar():
    url = request.form.get('url')
    
    if not url:
        return jsonify({'error': 'No se proporcionó URL'}), 400
    
    try:
        filename = descargar_con_api(url)
        
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
