from flask import Flask, render_template, request, Response
import yt_dlp
import subprocess
import urllib.parse
import imageio_ffmpeg as ffmpeg_lib

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/descargar')
def download():
    video_url = request.args.get('url')
    if not video_url:
        return "Falta la URL de la canción", 400

    # Configuración limpia y libre de cookies para SoundCloud
    ydl_opts = {
        'format': 'bestaudio/best',
        'nocheckcertificate': True,
        'quiet': True,
        'no_warnings': True,
        'skip_download': True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            url_directa = info.get('url')
            titulo_original = info.get('title', 'musica_descargada')
            
            if not url_directa:
                return "No se pudo extraer el flujo de audio de esta plataforma", 500

            nombre_archivo = "".join([c for c in titulo_original if c.isalpha() or c.isdigit() or c in ' ._-']).strip()
            nombre_archivo = f"{nombre_archivo}.mp3"
            nombre_codificado = urllib.parse.quote(nombre_archivo)

            ruta_ffmpeg = ffmpeg_lib.get_ffmpeg_exe()

            def generar_audio():
                comando_ffmpeg = [
                    ruta_ffmpeg, '-y', '-i', url_directa,
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

            headers = {
                'Content-Disposition': f"attachment; filename*=UTF-8''{nombre_codificado}",
                'Content-Type': 'audio/mpeg'
            }
            
            return Response(generar_audio(), headers=headers)

    except Exception as e:
        print(f"Error general: {e}")
        return f"Error al procesar el enlace. Asegúrate de ingresar un enlace válido: {e}", 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
