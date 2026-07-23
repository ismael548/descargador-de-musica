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

    # SOLUCIÓN: Eliminamos la clave 'format' de aquí para que NO exija formatos rígidos de entrada
    ydl_opts = {
        'nocheckcertificate': True,
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
        'cookiefile': 'cookies.txt'
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extraemos la información sin restricciones de formato
            info = ydl.extract_info(video_url, download=False)
            
            # Buscamos la URL directa del flujo multimedia entregado por YouTube
            url_directa = info.get('url')
            
            # Si el video tiene múltiples formatos combinados, buscamos en la lista de formatos disponibles
            if not url_directa and 'formats' in info:
                # Filtrar preferiblemente los que tengan solo audio o el primero disponible
                formatos_audio = [f for f in info['formats'] if f.get('vcodec') == 'none']
                if formatos_audio:
                    url_directa = formatos_audio[-1].get('url')  # Toma el de mejor calidad de audio
                else:
                    url_directa = info['formats'][0].get('url')   # Toma cualquier formato de respaldo

            titulo_original = info.get('title', 'musica_descargada')
            
            if not url_directa:
                return "No se pudo extraer ningún flujo de audio o video válido de este enlace", 500

            # Limpieza del título para la descarga estándar en Windows/Android
            nombre_archivo = "".join([c for c in titulo_original if c.isalpha() or c.isdigit() or c in ' ._-']).strip()
            nombre_archivo = f"{nombre_archivo}.mp3"
            nombre_codificado = urllib.parse.quote(nombre_archivo)

            ruta_ffmpeg = ffmpeg_lib.get_ffmpeg_exe()

            # El motor FFmpeg se encarga de transformar cualquier flujo de entrada a un estándar MP3
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
        print(f"Error general en el proceso: {e}")
        return f"Error interno en el servidor: {e}", 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)

