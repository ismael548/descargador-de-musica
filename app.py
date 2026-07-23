from flask import Flask, render_template, request, redirect
import urllib.parse
import re

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
        # 1. Extracción del ID usando una Expresión Regular profesional (Soporta youtu.be, watch?v= y shorts/)
        patron = r'(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/|youtube\.com\/shorts\/)([a-zA-Z0-9_-]{11})'
        resultado = re.search(patron, video_url)
        
        if not resultado:
            return "Por favor, ingresa un enlace válido de YouTube, Shorts o Youtube Music", 400
            
        video_id = resultado.group(1)

        # 2. Construimos la URL limpia de YouTube
        url_limpia = f"https://youtube.com{video_id}"
        
        # 3. Consumimos una API de redirección directa de alta disponibilidad (Inmune a los bloqueos de Render)
        api_redireccion = f"https://vexdwn.com{urllib.parse.quote(url_limpia)}&format=mp3"

        # 4. Redirigimos al navegador del usuario directamente al enlace final del MP3
        return redirect(api_redireccion)

    except Exception as e:
        return f"Error crítico al procesar la ruta de descargas: {e}", 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
