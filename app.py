from flask import Flask, render_template, request, Response
import yt_dlp
import subprocess
import urllib.parse

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/descargar')
def download():
    video_url = request.args.get('url')
    if not video_url:
        return "Falta la URL de la canción", 400

    ydl_opts = {
        'format': 'bestaudio/best',
        'nocheckcertificate': True,
        'quiet': True,
        'no_warnings': True,
        'skip_download': True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # 1. Extraemos los metadatos primero para obtener el título real de la canción
            info = ydl.extract_info(video_url, download=False)
            url_directa = info.get('url')
            titulo_original = info.get('title', 'musica_descargada')
            
            if not url_directa:
                return "No se pudo extraer el flujo de audio", 500

            # Limpiamos el título quitando caracteres extraños para evitar fallos en la descarga
            nombre_archivo = "".join([c for c in titulo_original if c.isalpha() or c.isdigit() or c in ' ._-']).strip()
            nombre_archivo = f"{nombre_archivo}.mp3"

            # Formateamos el nombre de forma segura para las cabeceras HTTP (evita problemas con acentos o eñes)
            nombre_codificado = urllib.parse.quote(nombre_archivo)

            # 2. Función generadora de transmisión binaria en vivo
            def generar_audio():
                comando_ffmpeg = [
                    'ffmpeg', '-y', '-i', url_directa,
                    '-f', 'mp3', '-acodec', 'libmp3lame', '-ab', '192k', '-'
                ]
                
                proceso = subprocess.Popen(
                    comando_ffmpeg,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                    bufsize=10**6
                )
                
                while True:
                    chunk = proceso.stdout.read(4096)
                    if not chunk:
                        break
                    yield chunk
                    
                proceso.stdout.close()
                proceso.wait()

            # 3. Cabeceras HTTP dinámicas con el nombre real de la canción
            headers = {
                'Content-Disposition': f"attachment; filename*=UTF-8''{nombre_codificado}",
                'Content-Type': 'audio/mpeg'
            }
            
            return Response(generar_audio(), headers=headers)

    except Exception as e:
        print(f"Error general en el proceso: {e}")
        return f"Error interno en el servidor: {e}", 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)

