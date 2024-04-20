import requests # type: ignore
from time import sleep
import json
from random import choice


# ATTENZIONE! Meta fornisce un short-lived access token (durata di qualche ora). E' necessario scambiarlo con un long-lived access token (durata c.a. 60 giorni)
# attraverso la seguente GET request.

def refresh_token(config_path):
    """
    Aggiorna l'access token per l'utilizzo dell'API di Instagram.
    :param config_path: Percorso del file JSON di configurazione.
    La funzione carica le informazioni di configurazione da 'config_path', utilizza il token attuale per ottenere 
    un nuovo token tramite una richiesta GET all'API di Facebook, quindi aggiorna il token nel file di configurazione.
    Gestisce eventuali errori durante il processo e stampa informazioni di debug.
    """
    # Caricamento config    
    with open(config_path) as c:
        config  = json.load(c)

    api_version = config["page_info"]["api_version"]

    refresh_token_url = f"https://graph.facebook.com/{api_version}/oauth/access_token"
    payload = {
        "grant_type": "fb_exchange_token",
        "client_secret": config["page_info"]["client_secret"], # secret key della app (su meta developers)        
        "client_id": config["page_info"]["client_id"], #config["page_info"]["client_id"], # ID della app (su meta developers)        
        "fb_exchange_token": config["page_info"]["access_token"] # Vecchio token, da refreshare
    }
    # Invio la richiesta
    print("Aggiornamento token.")
    r = requests.get(refresh_token_url, params=payload)
    print(r.request.body)
    sleep(.5)
    print(r.text)
    result = json.loads(r.text)
    try:
        if 'access_token' in result.keys():
            print("Token aggiornato con successo")
            print("\n")
            durata_res = result['expires_in']/60/60/24
            print(f"Durata residua del nuovo token: {durata_res} giorni")

            config["page_info"]["access_token"] = result["access_token"]
            with open(config_path, "w") as c:
                json.dump(config, c, indent=4)
        else:
            print(result)
            raise Exception("E03: Aggiornamento token fallito.")
    except:
        print("Aggiornamento token fallito.\nIl contenuto verrà postato ugualmente ma segnalare il problema a Riccardo.")
    


def publish_story(image_url, config_path):
    """
    Utilizza l'API di Instagram per pubblicare una storia.
    :param image_url: URL dell'immagine da pubblicare nella storia.
    :param config_path: Percorso del file JSON di configurazione.
    La funzione carica le informazioni di configurazione da 'config_path', 
    crea una storia su Instagram e la pubblica definitivamente.
    Gestisce eventuali errori e aggiorna il token di accesso.
    """ 

    # Caricamento config
    with open(config_path) as c:
        config  = json.load(c)

    # Definizione variabili
    ig_user_id = config["page_info"]["ig_user_id"]
    api_version = config["page_info"]["api_version"]
    media_type = "STORIES"

    post_content_step1 = f"https://graph.facebook.com/{api_version}/{ig_user_id}/media"

    # Contenuto della richiesta 1
    payload_step1 = {
        "image_url": image_url,
        "access_token": config["page_info"]["access_token"],
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
            "access_token": config["page_info"]["access_token"]
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

    # Aggiornamento del token
    refresh_token(config_path)

def publish_post_single(image_url, caption, config_path):
    """
    Utilizza l'API di Instagram per pubblicare un post.
    :param image_url: URL dell'immagine da pubblicare.
    :param caption: Didascalia del post.
    :param config_path: Percorso del file JSON di configurazione.
    La funzione carica le informazioni di configurazione da 'config_path', 
    crea un contenitore per il post su Instagram e lo pubblica definitivamente.
    Gestisce eventuali errori e aggiorna il token di accesso.
    """

    # Caricamento config
    with open(config_path) as c:
        config  = json.load(c)

    ig_user_id = config["page_info"]["ig_user_id"]
    api_version = config["page_info"]["api_version"]

    post_content_step1 = f"https://graph.facebook.com/{api_version}/{ig_user_id}/media"

    # Contenuto della richiesta 1
    payload_step1 = {
        "image_url": image_url,
        "caption": caption,
        "access_token": config["page_info"]["access_token"]
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
            "access_token": config["page_info"]["access_token"]
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

    # Aggiornamento del token
    refresh_token(config_path)







# -------------- TEST ---------------

# Caricamento immagini di test
with open("test_images.txt", "r") as i:
    test_images = [l.strip() for l in i]
config_path = "config.json"
# publish_story(choice(test_images), config, config_path)
publish_post_single(choice(test_images), "Test pubblicazione post singolo", config_path)


# def publish_post_multiple(): 
#     print("DA FARE")


