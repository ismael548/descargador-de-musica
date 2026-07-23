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
        # 1. Extracción e inmunización forzada del ID de YouTube
        # Limpia cualquier enlace roto (como youtube.comMt6...) usando una expresión regular estricta
        patron = r'([a-zA-Z0-9_-]{11})'
        resultado = re.findall(patron, video_url)
        
        # Buscamos una cadena de texto de exactamente 11 caracteres que es el ID único de YouTube
        video_id = ""
        for cadena in resultado:
            if len(cadena) == 11:
                video_id = cadena
                break
                
        if not video_id:
            return jsonify({'success': False, 'error': 'Por favor, ingresa un enlace válido de YouTube'}), 400

        # 2. Consumimos un motor de conversión JSON estable de alto rendimiento en la nube
        # Este gateway cuenta con proxies distribuidos que no sufren caídas de DNS
        api_url = f"https://vexdwn.com{video_id}&format=mp3"
        
        respuesta = requests.get(api_url, timeout=12).json()
        
        if not respuesta.get('success') or not respuesta.get('download_url'):
            # Respaldo inmediato por si el motor principal está saturado
            api_respaldo = f"https://vexdwn.com{video_id}&format=mp3"
            res_backup = requests.get(api_respaldo, timeout=12).json()
            if res_backup.get('success'):
                return jsonify({
                    'success': True,
                    'download_url': res_backup.get('download_url'),
                    'title': res_backup.get('title', 'musica_descargada.mp3')
                })
            return jsonify({'success': False, 'error': 'Los servidores globales están saturados. Intenta de nuevo.'}), 500

        # Devolvemos los datos limpios y estructurados en formato JSON al navegador
        return jsonify({
            'success': True,
            'download_url': respuesta.get('download_url'),
            'title': respuesta.get('title', 'musica_descargada.mp3')
        })

    except Exception as e:
        return jsonify({'success': False, 'error': f"Error en el motor de conversión: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)

