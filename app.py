from flask import Flask, render_template, request, jsonify
import requests

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
        # Limpieza manual y segura de la URL para extraer el ID de YouTube
        video_id = ""
        if "youtu.be/" in video_url:
            # Separa por youtu.be/ y toma la parte de la derecha, luego limpia si tiene signos "?"
            partes = video_url.split("youtu.be/")
            if len(partes) > 1:
                video_id = partes[1].split("?")[0]
        elif "v=" in video_url:
            partes = video_url.split("v=")
            if len(partes) > 1:
                video_id = partes[1].split("&")[0]
        elif "shorts/" in video_url:
            partes = video_url.split("shorts/")
            if len(partes) > 1:
                video_id = partes[1].split("?")[0]
        else:
            return jsonify({'success': False, 'error': 'Por favor, ingresa un enlace válido de YouTube'}), 400

        # Si no se pudo encontrar ningún ID limpio, frenamos el proceso
        if not video_id or len(video_id) != 11:
            return jsonify({'success': False, 'error': 'No se pudo identificar el ID del video'}), 400

        # Construimos la URL limpia de YouTube
        url_limpia = f"https://youtube.com{video_id}"

        # Consumimos el motor de conversión libre (Inmune a geobloqueos de Render)
        api_url = f"https://vexdwn.com{url_limpia}&format=mp3"
        
        # Realizamos la petición al convertidor
        respuesta = requests.get(api_url, timeout=15).json()
        
        # Validamos la respuesta del convertidor externo
        if not respuesta.get('success'):
            return jsonify({'success': False, 'error': 'El servidor de conversión está saturado. Intenta de nuevo.'}), 500

        # Devolvemos los datos limpios en formato JSON al JavaScript de tu HTML
        return jsonify({
            'success': True,
            'download_url': respuesta.get('download_url'),
            'title': respuesta.get('title', 'musica_descargada.mp3')
        })

    except Exception as e:
        return jsonify({'success': False, 'error': f"Error interno en el servidor: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
