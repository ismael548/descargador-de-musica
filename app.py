from flask import Flask, render_template, request, redirect
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

    try:
        # 1. Extracción del ID del video de YouTube de forma segura usando manipulación de texto limpia
        video_id = ""
        if "youtu.be/" in video_url:
            video_id = video_url.split("youtu.be/")[1].split("?")[0]
        elif "v=" in video_url:
            video_id = video_url.split("v=")[1].split("&")[0]
        elif "shorts/" in video_url:
            video_id = video_url.split("shorts/")[1].split("?")[0]
        else:
            return "Por favor, ingresa un enlace válido de YouTube o Shorts", 400

        # 2. EL TRUCO DEFINITIVO: Usamos una API de redirección directa de alta disponibilidad (Inmune a bloqueos de Render)
        # Reconstruimos el enlace limpio de YouTube para el motor de conversión
        url_limpia = f"https://youtube.com{video_id}"
        
        # Consumimos una pasarela de descarga directa que forzará la bajada del MP3 en el navegador del usuario
        api_redireccion = f"https://vexdwn.com{urllib.parse.quote(url_limpia)}&format=mp3"

        # 3. Redirigimos la ventana del usuario al enlace de la API.
        # De esta forma, el celular del usuario descarga la música directo del convertidor sin pasar por los servidores bloqueados de Render.
        return redirect(api_redireccion)

    except Exception as e:
        return f"Error crítico al procesar la ruta de descargas: {e}", 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
