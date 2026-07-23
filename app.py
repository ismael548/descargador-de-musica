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

    # SOLUCIÓN: Usamos 'ba' (bestaudio simplificado) o dejamos que extraiga el formato por defecto de audio plano
    ydl_opts = {
        'format': 'ba/bestaudio',  # Forzar a buscar un único flujo de audio básico sin mezclas de video
        'nocheckcertificate': True,
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
        'cookiefile': 'cookies.txt'
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extraer información del enlace
            info = ydl.extract_info(video_url, download=False)
            
            # Obtener URL directa
            url_directa = info.get('url')
            
            # Si yt-dlp entrega una lista en lugar de una URL única, extraemos el formato de respaldo
            if not url_directa and 'formats' in info:
                # Filtrar formatos que solo contengan audio (sin video)
                formatos_audio = [f for f in info['formats'] if f.get('vcodec') == 'none' and f.get('url')]
                if formatos_audio:
                    # Tomar el último formato de la lista (mejor calidad de audio disponible)
                    url_directa = formatos_audio[-1]['url']
                else:
                    # Si no hay filtros limpios, tomar la URL del primer formato general de la lista
                    url_directa = info['formats'][0]['url']

            titulo_original = info.get('title', 'musica_descargada')
            
            if not url_directa:
                return "No se pudo extraer ningún flujo de audio compatible de este enlace", 500

            # Limpieza y formateo del título para descarga en Windows/Android/iOS
            nombre_archivo = "".join([c for c in titulo_original if c.isalpha() or c.isdigit() or c in ' ._-']).strip()
            nombre_archivo = f"{nombre_archivo}.mp3"
            nombre_codificado = urllib.parse.quote(nombre_archivo)

            ruta_ffmpeg = ffmpeg_lib.get_ffmpeg_exe()

            # El motor FFmpeg procesará el flujo binario de audio de manera directa hacia el navegador
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
