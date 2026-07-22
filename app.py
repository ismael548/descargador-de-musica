from flask import Flask, render_template, request, send_file, jsonify
import requests
import os
import time

app = Flask(__name__)

DOWNLOAD_FOLDER = "downloads"
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

RAPIDAPI_KEY = "05792df5e0mshfc80c13c6697756p126763jsn45de2ded29ca"
RAPIDAPI_HOST = "youtube-to-mp315.p.rapidapi.com"


def descargar_con_rapidapi(youtube_url):
    """
    Usa RapidAPI para descargar MP3 de YouTube
    """
    
    api_url = f"https://{RAPIDAPI_HOST}/download"
    
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": RAPIDAPI_HOST,
        "Content-Type": "application/json"
    }
    
    params = {
        "url": youtube_url,
        "format": "mp3"
    }
    
    # Paso 1: Llamar a la API para iniciar conversión
    print(f"🔍 Enviando URL a RapidAPI: {youtube_url}")
    response = requests.post(api_url, headers=headers, params=params, timeout=60)
    
    print(f"📡 Status: {response.status_code}")
    
    if response.status_code != 200:
        raise Exception(f"Error API: {response.status_code}")
    
    result = response.json()
    print(f"📄 Respuesta: {result}")
    
    download_url = result.get("downloadUrl")
    
    if not download_url:
        raise Exception("La API no devolvió URL de descarga")
    
    # Paso 2: Esperar y reintentar descarga (hasta 10 intentos)
    max_attempts = 10
    wait_seconds = 3
    
    for attempt in range(1, max_attempts + 1):
        print(f"⏳ Intento {attempt}/{max_attempts} - Esperando {wait_seconds}s...")
        time.sleep(wait_seconds)
        
        print(f"⬇️ Descargando desde: {download_url}")
        mp3_response = requests.get(download_url, timeout=120)
        
        if mp3_response.status_code == 200 and len(mp3_response.content) > 1000:
            # Es un archivo MP3 válido
            timestamp = int(time.time())
            filename = f"cancion_{timestamp}.mp3"
            filepath = os.path.join(DOWNLOAD_FOLDER, filename)
            
            with open(filepath, "wb") as f:
                f.write(mp3_response.content)
            
            print(f"✅ Guardado: {filename} ({len(mp3_response.content)} bytes)")
            return filename
        
        print(f"⚠️ Aún no listo (Status: {mp3_response.status_code}, Size: {len(mp3_response.content)})")
    
    raise Exception("La conversión tardó demasiado. Intenta de nuevo en unos
