import requests
import configparser
import os

def get_api_key():
    config = configparser.ConfigParser()
    config_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'config.ini')
    config.read(config_path)
    
    api_key = config.get('ApiKeys', 'gpt_api_key', fallback=None)
    if not api_key:
        raise ValueError("API key not found in config file.")
    return str(api_key)

def chatgpt_api(data):
    endpoint_url = "https://api.openai.com/v1/chat/completions"
    your_api_key = get_api_key()
    
    headers = {
        "Authorization": "Bearer " + your_api_key
    }

    response = requests.post(url=endpoint_url, headers=headers, json=data)
    output_raw = response.json()
    output_message = output_raw['choices'][0]['message']['content']

    return output_raw, output_message

def create_language_learning_content(word, lang):
    data = {
        "model": "gpt-3.5-turbo-16k",
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful assistant that provides definitions, example sentences, and grammatical information about words."
            },
            {
                "role": "user",
                "content": f"""Provide a definition, and an example sentence in {lang} and English. Lastly, the grammatical type of the word '{word}' Maintain the format in the following example: 
                Definition: Progettazione (noun) - the act or process of designing or planning something, particularly in the field of architecture or engineering.
                Example sentence in Italian: La progettazione di un edificio richiede una pianificazione accurata.
                Example sentence in English: The design of a building requires careful planning.
                Grammatical type: Progettazione is a feminine singular noun in Italian."""
            }
        ],
        "temperature": 0.7
    }

    output_message = chatgpt_api(data)[1]
    return output_message
