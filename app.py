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
        # Extracción del ID limpia usando expresiones regulares universales
        patron = r'(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/|youtube\.com\/shorts\/)([a-zA-Z0-9_-]{11})'
        resultado = re.search(patron, video_url)
        
        if not resultado:
            return jsonify({'success': False, 'error': 'Por favor, ingresa un enlace válido de YouTube o Shorts'}), 400
            
        video_id = resultado.group(1)
        url_limpia = f"https://www.youtube.com/watch?v={video_id}"

        # Consumimos la infraestructura global de Cobalt (Inmune a geobloqueos)
        api_url = "https://cobalt.tools"
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        payload = {
            "url": url_limpia,
            "downloadMode": "audio",
            "audioFormat": "mp3",
            "audioBitrate": "192"
        }

        # Realizamos la petición POST al backend del convertidor
        respuesta = requests.post(api_url, json=payload, headers=headers, timeout=15).json()
        
        # Validamos si Cobalt nos entregó con éxito el archivo de audio procesado
        if respuesta.get('status') == 'error' or not respuesta.get('url'):
            return jsonify({'success': False, 'error': respuesta.get('text', 'El motor externo no pudo procesar este video')}), 500

        # Devolvemos los datos limpios en formato JSON al navegador del usuario
        return jsonify({
            'success': True,
            'download_url': respuesta.get('url'),
            'title': respuesta.get('filename', 'musica_descargada.mp3')
        })

    except Exception as e:
        return jsonify({'success': False, 'error': f"Error en la pasarela en la nube: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
