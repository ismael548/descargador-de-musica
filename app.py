from flask import Flask, render_template, request, send_file, jsonify
import requests
import os
import time

app = Flask(__name__)

DOWNLOAD_FOLDER = "downloads"
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

# Tu API Key de RapidAPI
RAPIDAPI_KEY = "05792df5e0mshfc80c13c6697756p126763jsn45de2ded29ca"
RAPIDAPI_HOST = "youtube-to-mp315.p.rapidapi.com"


def descargar_con_rapidapi(youtube_url):
    """
    Usa RapidAPI para descargar MP3 de YouTube
    """
    
    # URL de la API
    api_url = f"https://{RAPIDAPI_HOST}/download"
    
    # Headers
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": RAPIDAPI_HOST,
        "Content-Type": "application/json"
    }
    
    # Parámetros
    params = {
        "url": youtube_url,
        "format": "mp3"
    }
    
    # Paso 1: Llamar a la API para iniciar conversión
    print(f"🔍 Enviando URL a RapidAPI: {youtube_url}")
    response = requests.post(api_url, headers=headers, params=params, timeout=60)
    
    print(f"📡 Status: {response.status_code}")
    
    # La API devuelve JSON con el downloadUrl
    if response.status_code == 200:
        result = response.json()
        print(f"📄 Respuesta: {result}")
        
        download_url = result.get("downloadUrl")
        status = result.get("status")
        
        if not download_url:
            raise Exception("La API no devolvió URL de descarga")
        
        # Paso 2: Esperar si está CONVERTING y luego descargar
        if status == "CONVERTING":
            print("⏳ Esperando conversión...")
            time.sleep(5)  # Esperar 5 segundos
        
        # Paso 3: Descargar el MP3 desde la URL
        print(f"⬇️ Descargando desde: {download_url}")
        mp3_response = requests.get(download_url, timeout=120)
        
        if mp3_response.status_code != 200:
            raise Exception(f"No se pudo descargar el MP3: {mp3_response.status_code}")
        
        # Guardar archivo
        timestamp = int(time.time())
        filename = f"cancion_{timestamp}.mp3"
        filepath = os.path.join(DOWNLOAD_FOLDER, filename)
        
        with open(filepath, "wb") as f:
            f.write(mp3_response.content)
        
        print(f"✅ Guardado: {filename} ({len(mp3_response.content)} bytes)")
        return filename
    
    else:
        raise Exception(f"Error API: {response.status_code}")


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/descargar', methods=['POST'])
def descargar():
    url = request.form.get('url')
    
    if not url:
        return jsonify({'error': 'No se proporcionó URL'}), 400
    
    # Validar que sea URL de YouTube
    if 'youtube.com' not in url and 'youtu.be' not in url:
        return jsonify({'error': 'Solo se soportan URLs de YouTube'}), 400
    
    try:
        filename = descargar_con_rapidapi(url)
        
        return jsonify({
            'success': True,
            'mensaje': '¡Descarga completada!',
            'archivo': filename
        })
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/descargar_archivo/<nombre>')
def descargar_archivo(nombre):
    ruta = os.path.join(DOWNLOAD_FOLDER, nombre)
    if not os.path.exists(ruta):
        return jsonify({'error': 'Archivo no encontrado'}), 404
    return send_file(ruta, as_attachment=True)


if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
