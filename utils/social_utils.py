import json
from time import sleep
import requests

def publish_story(image_url, config):
    """
    Utilizza l'API di Instagram per pubblicare una storia.
    :param image_url: URL dell'immagine da pubblicare nella storia.
    :param config_path: Percorso del file JSON di configurazione.
    La funzione carica le informazioni di configurazione da 'config_path', 
    crea una storia su Instagram e la pubblica definitivamente.
    Gestisce eventuali errori e aggiorna il token di accesso.
    """ 

    # Definizione variabili
    ig_user_id = config["ig_user_id"]
    api_version = config["api_version"]
    media_type = "STORIES"

    post_content_step1 = f"https://graph.facebook.com/{api_version}/{ig_user_id}/media"

    # Contenuto della richiesta 1
    payload_step1 = {
        "image_url": image_url,
        "access_token": config["access_token"],
        "media_type": media_type
    }

    # Invio la richiesta
    r = requests.post(post_content_step1, data=payload_step1)
    sleep(.5)
    print(r.text)

    result_step1 = json.loads(r.text)
    
    if 'id' in result_step1.keys():
        creation_id = result_step1['id']

        post_content_step2 = f"https://graph.facebook.com/{api_version}/{ig_user_id}/media_publish"

        # Contenuto della richiesta 2
        payload_step2 = {
            "creation_id": creation_id,
            "access_token": config["access_token"]
        }

        # Invio la richiesta
        r = requests.post(post_content_step2, data=payload_step2)
        sleep(.5)
        print(r.text)
        result_step2 = json.loads(r.text)
        if 'id' in result_step2.keys():
            print("Postato con successo su Instagram.")
        else:
            print(result_step2)
            raise Exception("E02: La richiesta di postare non è andata a buon fine.")
    else:
        print(result_step1)
        raise Exception("E01: La richiesta di postare non è andata a buon fine.")

    # # Aggiornamento del token
    # refresh_token(config_path)


def publish_post(): ...
