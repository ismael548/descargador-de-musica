from flask import Flask, render_template, request, Response, jsonify
import requests

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/descargar')
def download():
    video_url = request.args.get('url')
    if not video_url:
        return "Falta la URL de la canción", 400

    try:
        # LÍNEA CORREGIDA: La URL de la API ahora está limpia y estructurada de forma correcta
        api_url = "https://vexdwn.com"
        parametros = {
            'url': video_url,
            'format': 'mp3'
        }
        
        # Realizamos la petición pasando los parámetros de forma limpia
        respuesta_api = requests.get(api_url, params=parametros, timeout=15).json()
        
        if not respuesta_api.get('success'):
            return "El convertidor externo no pudo procesar este enlace. Intenta con otro.", 500
            
        url_archivo_mp3 = respuesta_api.get('download_url')
        titulo_cancion = respuesta_api.get('title', 'musica_descargada')

        # Descargamos el archivo procesado desde la API y lo transmitimos en vivo al usuario
        def generar_audio():
            with requests.get(url_archivo_mp3, stream=True) as r:
                r.raise_for_status()
                for chunk in r.iter_content(chunk_size=4096):
                    if chunk:
                        yield chunk

        # Formateamos el nombre del archivo para el dispositivo del usuario
        nombre_archivo = "".join([c for c in titulo_cancion if c.isalpha() or c.isdigit() or c in ' ._-']).strip()
        headers = {
            'Content-Disposition': f"attachment; filename*=UTF-8''{nombre_archivo}.mp3",
            'Content-Type': 'audio/mpeg'
        }
        
        return Response(generar_audio(), headers=headers)

    except Exception as e:
        return f"Error al conectar con el motor de descargas en la nube: {e}", 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)


