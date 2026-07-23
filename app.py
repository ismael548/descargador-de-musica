from flask import Flask, render_template, request, jsonify
import requests
import re

app = Flask(__name__)

# Configuración de RapidAPI - Ajusta estos valores según la API de YouTube que elijas en RapidAPI
# Por ejemplo, si usas "YouTube MP36", el host es "youtube-mp36.p.rapidapi.com" y el endpoint es "/dl"
RAPIDAPI_KEY = "TU_CLAVE_DE_RAPIDAPI_AQUÍ"  # ⚠️ REEMPLAZA CON TU KEY REAL DE RAPIDAPI
RAPIDAPI_HOST = "youtube-mp36.p.rapidapi.com" # Cambia esto según la API que uses
API_URL = "https://youtube-mp36.p.rapidapi.com/dl" # Endpoint de la API

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/descargar')
def download():
    video_url = request.args.get('url')
    if not video_url:
        return jsonify({'success': False, 'error': 'Falta la URL de la canción'}), 400

    try:
        # Extracción limpia del ID del video
        patron = r'(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/|youtube\.com\/shorts\/)([a-zA-Z0-9_-]{11})'
        resultado = re.search(patron, video_url)
        
        if not resultado:
            return jsonify({'success': False, 'error': 'Por favor, ingresa un enlace válido de YouTube'}), 400
            
        video_id = resultado.group(1)
        
        # Corregido: Agregada la barra diagonal "/" que faltaba para formar una URL válida
        url_limpia = f"https://www.youtube.com/watch?v={video_id}"

        # Pasarela segura con tu clave privada
        headers = {
            "x-rapidapi-key": RAPIDAPI_KEY,
            "x-rapidapi-host": RAPIDAPI_HOST
        }
        
        # Algunas APIs de RapidAPI piden el parámetro 'id' en lugar de 'url' (ej. YouTube MP36)
        # Adaptamos los parámetros a lo que necesite tu API específica.
        parametros = {'id': video_id}  # Si tu API usa 'url', cambia 'id' por 'url' y usa 'url_limpia'

        respuesta_http = requests.get(API_URL, params=parametros, headers=headers, timeout=15)
        
        # Validación de respuesta HTTP antes de intentar decodificar JSON
        if respuesta_http.status_code != 200:
            return jsonify({
                'success': False,
                'error': f"Error de RapidAPI (Código {respuesta_http.status_code}): {respuesta_http.text[:100]}"
            }), 500

        try:
            respuesta = respuesta_http.json()
        except ValueError:
            return jsonify({
                'success': False,
                'error': "La API externa no devolvió un formato JSON válido. Verifica la configuración."
            }), 500
        
        # Extraemos el enlace de descarga y el título
        url_descarga = respuesta.get('link') or respuesta.get('downloadUrl') or respuesta.get('url')
        titulo = respuesta.get('title', 'musica_descargada.mp3')
        
        if not url_descarga:
            return jsonify({
                'success': False, 
                'error': f"La API no devolvió un enlace de descarga. Respuesta recibida: {respuesta}"
            }), 500

        return jsonify({
            'success': True,
            'download_url': url_descarga,
            'title': titulo
        })

    except Exception as e:
        return jsonify({'success': False, 'error': f"Error en el motor de conversión: {str(e)}"}), 500

if __name__ == '__main__':
    import os
    # Render asigna dinámicamente un puerto en la variable de entorno PORT.
    # También es obligatorio enlazar a la dirección 0.0.0.0 para que sea accesible externamente.
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
