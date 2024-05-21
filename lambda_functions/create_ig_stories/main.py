from image_editing import image_edit

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
    img_path = "test_img.png"

    # da fare:
    # https://stackoverflow.com/questions/1970807/center-middle-align-text-with-pil
    # https://pillow.readthedocs.io/en/stable/handbook/text-anchors.html
    # - scegliere colore testo parametrico, adatto all'immagine
    #   - non funziona, non c'è un algoritmo per scegliere il migliore colore. Meglio usare bianco con outline nero
    # - aggiungere icone per luogo, data, ora, costo etc. e metterle a sx del testo
    # - aggiungere sezione contatti

    edit_dict = {
        "title": {"text": "Torneo di Bang",
                  "font": "montserratalternates/MontserratAlternates-Bold.ttf",
                  "size": 70, 
                  "color": (255, 255, 255),
                  "anchor":"mm"},
        "body": {"text": "Divertiti con noi al più famoso gioco western!",
                  "font": "montserratalternates/MontserratAlternates-Bold.ttf",
                  "size": 40, 
                  "color": (255, 255, 255),
                  "anchor":"mm"},        
        "date": {"text": "Mercoledì 31 febbraio",
                  "font": "montserratalternates/MontserratAlternates-Bold.ttf",
                  "size": 40, 
                  "color": (255, 255, 255),
                  "anchor":"lm"},
        "time": {"text": "21:00",
                  "font": "montserratalternates/MontserratAlternates-Bold.ttf",
                  "size": 40, 
                  "color": (255, 255, 255),
                  "anchor":"lm"},
        "location": {"text": "Centro NOI di Povegliano",
                  "font": "montserratalternates/MontserratAlternates-Bold.ttf",
                  "size": 40, 
                  "color": (255, 255, 255),
                  "anchor":"lm"},
        "cost": {"text": "Iscrizione libera",
                  "font": "montserratalternates/MontserratAlternates-Bold.ttf",
                  "size": 40, 
                  "color": (255, 255, 255),
                  "anchor":"lm"}
    }

    img_path_edit = image_edit(img_path, edit_dict)
    # ----------------------------

    # ----------------------------
    # caricamento immagine su imgur per ottenere url
    
    # ----------------------------

    # ----------------------------
    # post storia ig
        # ritornare messaggio di successo o eventuale errore
    # ----------------------------






    return {"statusCode": 200, "body": "Elaboration completed"}




if __name__ == "__main__":

    lambda_handler(1,2)