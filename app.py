from flask import Flask, render_template, request, jsonify
import requests
import re

app = Flask(__name__)

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
        url_limpia = f"https://youtube.com{video_id}"

        # Pasarela segura con tu clave privada
        api_url = "https://rapidapi.com"
        parametros = {'url': url_limpia}
        headers = {
            # REEMPLAZA ESTE TEXTO CON TU KEY REAL DE RAPIDAPI
            "x-rapidapi-key": "TU_CLAVE_DE_RAPIDAPI_AQUÍ",
            "x-rapidapi-host": "://rapidapi.com"
        }
        
        respuesta = requests.get(api_url, params=parametros, headers=headers, timeout=15).json()
        
        url_descarga = respuesta.get('downloadUrl')
        titulo = respuesta.get('title', 'musica_descargada.mp3')
        
        if not url_descarga:
            return jsonify({'success': False, 'error': 'Error al procesar el archivo multimedia.'}), 500

        return jsonify({
            'success': True,
            'download_url': url_descarga,
            'title': titulo
        })

    except Exception as e:
        return jsonify({'success': False, 'error': f"Error en el motor de conversión: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)

