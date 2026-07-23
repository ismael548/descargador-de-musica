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
        # Expresión regular robusta para capturar los 11 caracteres exactos del ID de YouTube
        patron = r'(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/|youtube\.com\/shorts\/)([a-zA-Z0-9_-]{11})'
        resultado = re.search(patron, video_url)
        
        if not resultado:
            return jsonify({'success': False, 'error': 'Por favor, ingresa un enlace válido de YouTube o Shorts'}), 400
            
        video_id = resultado.group(1)
        url_limpia = f"https://www.youtube.com/watch?v={video_id}"

        # Consumimos una API JSON nativa avanzada para desarrolladores
        api_url = f"https://socialdownload.to{url_limpia}&format=mp3"
        
        # Realizamos la petición en segundo plano desde el backend de Render
        respuesta = requests.get(api_url, timeout=15).json()
        
        if not respuesta.get('success') or not respuesta.get('download_url'):
            # API de respaldo directa por si el servidor principal experimenta alta latencia
            api_respaldo = f"https://vexdwn.com{url_limpia}&format=mp3"
            res_backup = requests.get(api_respaldo, timeout=12).json()
            if res_backup.get('success'):
                return jsonify({
                    'success': True,
                    'download_url': res_backup.get('download_url'),
                    'title': res_backup.get('title', 'musica_descargada.mp3')
                })
            return jsonify({'success': False, 'error': 'Los servidores de conversión están saturados. Intenta más tarde.'}), 500

        # Devolvemos los datos limpios en formato JSON al navegador del usuario
        return jsonify({
            'success': True,
            'download_url': respuesta.get('download_url'),
            'title': respuesta.get('title', 'musica_descargada.mp3')
        })

    except Exception as e:
        return jsonify({'success': False, 'error': f"Error interno en el servidor: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
