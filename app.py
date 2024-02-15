from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
import difflib
import openai
from flask_cors import CORS  # Importa la extensión
import random
import os
import pyttsx3



app = Flask(__name__)
CORS(app)  # Habilita CORS para la aplicación

openai.api_key = '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'  # Reemplaza con tu clave de API de OpenAI

def text_to_speech(text, language='es', speed=200, filename='response.mp3', voice=1):
    # Crear un objeto de la clase TextToSpeech
    engine = pyttsx3.init()

    # Configurar la velocidad del habla
    engine.setProperty('rate', speed)

    voices = engine.getProperty('voices')
    engine.setProperty('voice', voices[0].id)      # Change index to change voice. 0 for male and 1 for female

    # Configurar el idioma (opcional, dependiendo de tu configuración)
    engine.setProperty('voice', f'{language}')

    # Guardar el audio en un archivo
    engine.save_to_file(text, filename)

    # Ejecutar la conversión de texto a voz
    engine.runAndWait()



# Definir la ruta para manejar las solicitudes POST
@app.route('/ask', methods=['POST'])
def ask():
    data = request.get_json()
    user_input = data.get('user_input')

    # Lista de palabras clave que indican preguntas para el asistente virtual
    palabras_clave_asistente_virtual = ["tu objetivo", "quien es tu creador", "quien te ha creado", "por quien fuiste creado", "ey", "oye", "escribe un codigo", "presentate", "quien eres", "hola", "tal", "como te llamas", "tu nombre", "resume", "hazme un resumen", "resúmeme", "cuentame algo sobre ti", "cuentame", "eres", "bien y tu"]

    # Verificar si la pregunta es una interacción normal con el asistente virtual
    interaccion_normal = any(keyword in user_input.lower() for keyword in palabras_clave_asistente_virtual)

    if interaccion_normal:
        
        # Si es una interacción normal, simplemente utiliza GPT-3 para generar una respuesta

        # Utilizar GPT-3 para generar una respuesta basada
        gpt3_prompt = f"Responde con carisma y de manera humana {user_input}\n"
        gpt3_response = generate_response(user_input, "", gpt3_prompt)
        text_to_speech(gpt3_response)  # Convertir respuesta a voz

        # Devolver la respuesta como parte de la respuesta JSON
        return jsonify({"response": gpt3_response, "audio": "response.mp3"})
    else:
        # Si no es una interacción normal, realiza la búsqueda en DuckDuckGo y muestra resultados
        # (puedes personalizar esta parte según tus necesidades)
        search_results = search_duckduckgo(user_input)
        most_relevant_link = get_most_relevant_link(user_input, search_results)

        if most_relevant_link:
            page_content = get_page_content(most_relevant_link)
            # Utilizar GPT-3 para generar una respuesta basada


            gpt3_prompt = f"Formula una respuesta con carisma y humana en base a lo siguiente y imprime el enlace mas relevante: Enlace mas relevante:{most_relevant_link} Input usuario: {user_input}\nResponde en base a esto: {' '.join(page_content)}"


            gpt3_response = generate_response(user_input, "", gpt3_prompt)
            text_to_speech(gpt3_response)  # Convertir respuesta a voz
            return jsonify({"response": gpt3_response, "audio": "response.mp3"})
        else:
            return jsonify({"response": "No se encontraron resultados relevantes en Internet.", "audio": None})

# Manejar el error "Method Not Allowed"
@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({"error": "Método no permitido. Utiliza una solicitud POST en la ruta /ask."}), 405

def search_duckduckgo(query, max_results=5):
    with DDGS() as ddgs:
        results = [r for r in ddgs.text(query, max_results=max_results)]
    return results

def get_most_relevant_link(user_input, search_results):
    if not search_results:
        return None

    titles = [result.get('title') for result in search_results]
    similarity_scores = [difflib.SequenceMatcher(None, user_input, title).ratio() for title in titles]
    most_relevant_index = similarity_scores.index(max(similarity_scores))

    return search_results[most_relevant_index].get('href')

def get_page_content(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:97.0) Gecko/20100101 Firefox/97.0"
    }
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    for header in soup.find_all(['header', 'nav']):
        header.decompose()
    for footer in soup.find_all('footer'):
        footer.decompose()

    paragraphs = [p.text for p in soup.find_all('p')]

    return paragraphs

def generate_response(user_input, user_context, assistant_context):
    max_prompt_length = 4096
    truncated_prompt = user_input[:max_prompt_length]

    # Define una temperatura aleatoria entre 0.2 y 0.8
    temperature = round(random.uniform(0.2, 0.8), 1)

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-0125",
        messages=[
            {"role": "system", "content": "Te llamas asai, eres vacilon, y eres un compañero virtual, usas expresiones como: que pasa tio, como estas. Tu creador es uri y te desarolló en 2024. "},
            {"role": "user", "content": user_context + truncated_prompt},
            {"role": "assistant", "content": assistant_context}
        ],
        # Añade la temperatura al request
        temperature=temperature
    )

    gpt3_response = response['choices'][0]['message']['content'].strip()

    return gpt3_response

if __name__ == '__main__':
    app.run(debug=True)
