from image_editing import image_edit
from imgur_functions import load_imgur
from meta_functions import publish_story
import utils.aws_utils as aws_utils # ricordati di spostare utils in lambda_functions

META_CLIENT_SECRET = aws_utils.get_parameters(
    parameter_name="/meta/client-secret", is_secure=True#, ssm_client=ssm_client
)

META_ACCESS_TOKEN = aws_utils.get_parameters(
    parameter_name="/meta/access-token", is_secure=True#, ssm_client=ssm_client
)

def lambda_handler(event: dict, context):
    """
    event = {"event_id": "1234567890"}
    
    """
    # ----------------------------
    # prendere da dynamo la riga corrispondente a event_id
    # event_info = {}
    # ----------------------------

    # ----------------------------
    # generazione immagine 
        # salvataggio immagine su img_path
    # ----------------------------



    # ----------------------------
    # edit immagine con testo
        # crop to aspect ratio 9:16
        # salvataggio immagine su img_path_edit

    # provare su aws s3 a caricare un file e creare un url presigned

    EVENT_TYPE = {
        ""
    }


    img_path = "test_img.png"



    edit_dict = {
        "title": {"text": "Torneo di Bang",
                  "size": 70, 
                  "anchor":"mm"},
        "description": {"text": "Divertiti con noi al più famoso gioco western!",
                  "size": 40, 
                  "anchor":"mm"},        
        "date": {"text": "Mercoledì 31 febbraio",
                  "size": 40, 
                  "anchor":"lm"},
        "time": {"text": "21:00",
                  "size": 40, 
                  "anchor":"lm"},
        "location": {"text": "Centro NOI di Povegliano",
                  "size": 40, 
                  "anchor":"lm"},
        "cost": {"text": "Iscrizione libera",
                  "size": 40, 
                  "anchor":"lm"}
        # "other_info": se non ci sono "na"
    }
    print("Editing immagine in corso.")
    img_path_edit = image_edit(img_path, edit_dict)
    # ----------------------------

    # ----------------------------
    # caricamento immagine su imgur per ottenere url

    imgur_config = {
                        "imgur_client_id": "a479ab6df29945b",
                        "imgur_client_secret": "2683b21fc6bfc8705508a487ed04b169c8d092c0"
                    } # da mettere nel gestore parametri
    print("Caricamento immagine su imgur.")
    img_url = load_imgur(imgur_config, img_path_edit)
    print(img_url)
    # ----------------------------

    # ----------------------------
    # post storia ig
        # ritornare messaggio di successo o eventuale errore
    meta_config = {
        "fb_page_id": "317629034756571",
        "ig_user_id": "17841465940733845",
        "client_id": "1816564495510379",
        "client_secret": META_CLIENT_SECRET,
        "api_version": "v19.0",
        "access_token": META_ACCESS_TOKEN
    }
    print("Pubblicazione storia Instagram in corso.")
    publish_story(img_url, meta_config)
    # ----------------------------






    return {"statusCode": 200, "body": "Elaboration completed"}




if __name__ == "__main__":

    lambda_handler(1,2)