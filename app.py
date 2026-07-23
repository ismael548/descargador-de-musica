from flask import Flask, render_template, request, Response
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
        # Extraemos el ID del video de YouTube desde la URL ingresada
        video_id = ""
        if "youtu.be/" in video_url:
            video_id = video_url.split("youtu.be/")[1].split("?")[0]
        elif "v=" in video_url:
            video_id = video_url.split("v=")[1].split("&")[0]
        else:
            return "Por favor, ingresa un enlace válido de YouTube", 400

        # Consumimos un motor de descarga con proxies residenciales integrados
        api_url = f"https://cobalt.tools"
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        payload = {
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "downloadMode": "audio",
            "audioFormat": "mp3",
            "audioBitrate": "192"
        }

        # Realizamos la petición POST al backend del convertidor
        respuesta = requests.post(api_url, json=payload, headers=headers, timeout=15).json()
        
        # Si la API Cobalt no responde, usamos una API de respaldo rápida
        if respuesta.get('status') == 'error' or not respuesta.get('url'):
            api_respaldo = f"https://vexdwn.com{video_id}&format=mp3"
            res_backup = requests.get(api_respaldo, timeout=12).json()
            url_archivo_mp3 = res_backup.get('download_url')
            titulo_cancion = res_backup.get('title', 'musica_descargada')
        else:
            url_archivo_mp3 = respuesta.get('url')
            titulo_cancion = respuesta.get('filename', 'musica_descargada')

        if not url_archivo_mp3:
            return "Ambos motores de descarga están saturados. Intenta de nuevo en unos minutos.", 500

        # Transmitimos el audio binario directamente al dispositivo del usuario
        def generar_audio():
            with requests.get(url_archivo_mp3, stream=True) as r:
                r.raise_for_status()
                for chunk in r.iter_content(chunk_size=4096):
                    if chunk:
                        yield chunk

        # Limpiamos el título quitando caracteres extraños para la descarga móvil
        nombre_archivo = "".join([c for c in titulo_cancion if c.isalpha() or c.isdigit() or c in ' ._-']).strip()
        
        headers_http = {
            'Content-Disposition': f"attachment; filename*=UTF-8''{nombre_archivo}.mp3",
            'Content-Type': 'audio/mpeg'
        }
        
        return Response(generar_audio(), headers=headers_http)

    except Exception as e:
        return f"Error crítico al conectar con el servidor de descargas: {e}", 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
