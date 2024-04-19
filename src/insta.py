import requests # type: ignore
from time import sleep
import json
from random import choice


# ATTENZIONE! Meta fornisce un short-lived access token (durata di qualche ora). E' necessario scambiarlo con un long-lived access token (durata c.a. 60 giorni)
# attraverso la seguente GET request.

def refresh_token(config, config_path):

    refresh_token_url = 'https://graph.facebook.com/v19.0/oauth/access_token'
    payload = {
        "client_secret": config["page_info"]["client_secret"], # secret key della app (su meta developers)
        "grant_type": 'fb_exchange_token',
        "client_id": '1816564495510379', #config["page_info"]["client_id"], # ID della app (su meta developers)        
        "fb_exchange_token": config["page_info"]["access_token"] # Vecchio token, da refreshare
    }
    # Invio la richiesta
    print("Aggiornamento token.")
    r = requests.get(refresh_token_url, data=payload)
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
                json.dump(config, c)
        else:
            print(result)
            raise Exception("E03: Aggiornamento token fallito.")
    except:
        print("Aggiornamento token fallito.\nIl contenuto verrà postato ugualmente ma segnalare il problema a Riccardo.")
    


def publish_story(image_url, config, config_path):
    api_version = "v19.0"
    media_type = "STORIES"

    ig_user_id = config["page_info"]["ig_user_id"]

    # Postare contenuti su ig richiede due step:
    # 1. mandare una POST request per creare il 'container' relativo al post/storia
    #   https://graph.facebook.com/v19.0/{ig_user_id}/media?image_url={image_url}&caption={caption}&access_token={access_token}&media_type={media_type}
    # 2. mandare una POST request per pubblicare definitivamente il post/storia
    #   https://graph.facebook.com/v19.0/{ig_user_id}/media_publish?creation_id={creation_id}&access_token={access_token}

    post_content_step1 = f"https://graph.facebook.com/{api_version}/{ig_user_id}/media"

    # Contenuto della richiesta 1
    payload_step1 = {
        "image_url": image_url,
        # "caption": caption,
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
    # refresh_token(config, config_path)

def publish_post_single(image_url, caption, config, config_path):
    api_version = "v19.0"

    ig_user_id = config["page_info"]["ig_user_id"]

    # Postare contenuti su ig richiede due step:
    # 1. mandare una POST request per creare il 'container' relativo al post/storia
    #   https://graph.facebook.com/v19.0/{ig_user_id}/media?image_url={image_url}&caption={caption}&access_token={access_token}&media_type={media_type}
    # 2. mandare una POST request per pubblicare definitivamente il post/storia
    #   https://graph.facebook.com/v19.0/{ig_user_id}/media_publish?creation_id={creation_id}&access_token={access_token}

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
    # refresh_token(config, config_path)


# Caricamento config
config_path = "config.json"
with open(config_path) as c:
    config  = json.load(c)

# Caricamento immagini di test
with open("test_images.txt", "r") as i:
    test_images = [l.strip() for l in i]

# publish_story(choice(test_images), config, config_path)
publish_post_single(choice(test_images), "Test pubblicazione post singolo", config, config_path)


# refresh_token_url = 'https://graph.facebook.com/v19.0/oauth/access_token'
# payload = {
#     'grant_type': 'fb_exchange_token', 
#     'client_id': '1816564495510379', #config["page_info"]["client_id"], # ID della app (su meta developers)      
#     'client_secret': '59c7f63fb73be9722023019017025b70', # secret key della app (su meta developers)     
#     'fb_exchange_token':'EAAZA0JZBF3a2sBO61jqFAFERrZAI4e0QjGyMGMJipfJy3SEXlJXE4GYSJvTZA8xeLzwJupxZAOzDvTK4BYxZCqqNhtIk70przJFAsihQgKJqmXFhZC50pkUO0L4bDEWgiRwsWcnPnw4VMwX4OGkPiplF7ODRrGCqrxhX2Cgv4xTbesHcSSbekKGMyH3w2otPI1W' # Vecchio token, da refreshare
# }
# # Invio la richiesta
# print("Aggiornamento token.")
# r = requests.get(refresh_token_url, data=payload)
# # print(r.request.body)
# print(r.text)



# def publish_post_single():
#     print("DA FARE")

# def publish_post_multiple(): 
#     print("DA FARE")

1816564495510379
1234567890123456


    # get_ig_id restituisce l'id dell'user ig. Se conosco già l'id non serve lanciarlo
    # get_ig_id = f"https://graph.facebook.com/v19.0/{fb_page_id}?fields=instagram_business_account&access_token={access_token}"