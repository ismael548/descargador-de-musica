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

    # SOLUCIÓN DE RAÍZ: Forzamos compatibilidad extrema simulando un reproductor web de escritorio
    ydl_opts = {
        'format': 'bestaudio/best',  # Volvemos al estándar compatible con streams HTTP
        'nocheckcertificate': True,
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
        'cookiefile': 'cookies.txt',
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-us,en;q=0.5'
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Intentamos la extracción directa con los headers simulados
            try:
                info = ydl.extract_info(video_url, download=False)
            except Exception as format_error:
                # CONTINGENCIA: Si falla por formato o IP restringida, obligamos a capturar cualquier flujo suelto
                print(f"Fallo de formato primario, activando respaldo: {format_error}")
                ydl_opts['format'] = 'worst/all'  # Fuerza la captura de cualquier cosa existente
                with yt_dlp.YoutubeDL(ydl_opts) as ydl_fallback:
                    info = ydl_fallback.extract_info(video_url, download=False)

            url_directa = info.get('url')
            
            # Navegamos en la lista de formatos plana de YouTube de forma segura si no hay URL directa
            if not url_directa and 'formats' in info:
                for f in info['formats']:
                    if f.get('url') and (f.get('vcodec') == 'none' or 'audio' in f.get('format_note', '').lower()):
                        url_directa = f['url']
                        break
                if not url_directa:
                    url_directa = info['formats'][0]['url']

            titulo_original = info.get('title', 'musica_descargada')
            
            if not url_directa:
                return "YouTube restringió los formatos de transmisión para la ubicación de este servidor en la nube.", 500

            # Formateo estricto del título del archivo MP3
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
        print(f"Error general en el proceso: {e}")
        return f"Error interno en el servidor (YouTube bloqueó este enlace en Render): {e}", 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
