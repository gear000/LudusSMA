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
    # - mettere posizione parametrica (e.g. titolo centrato)
    # - scegliere colore testo parametrico, adatto all'immagine


    edit_dict = {
        "title": {"text": "Torneo di Bang",
                  "font": "montserratalternates/MontserratAlternates-Bold.ttf",
                  "size": 90, 
                  "color": (55, 0, 134),
                  "position":(0,100)},
        "body": {"text": "",
                  "font": "montserratalternates/MontserratAlternates-Bold.ttf",
                  "size": 80, 
                  "color": (55, 0, 134),
                  "position":(0,0)},
        "location": {"text": "Centro NOI di Povegliano",
                  "font": "montserratalternates/MontserratAlternates-Bold.ttf",
                  "size": 40, 
                  "color": (55, 0, 134),
                  "position":(0,900)},
        "datetime": {"text": "Mercoledì 31 febbraio ore 21:00",
                  "font": "montserratalternates/MontserratAlternates-Bold.ttf",
                  "size": 40, 
                  "color": (55, 0, 134),
                  "position":(0,950)},
        "cost": {"text": "Iscrizione libera",
                  "font": "montserratalternates/MontserratAlternates-Bold.ttf",
                  "size": 40, 
                  "color": (55, 0, 134),
                  "position":(0,1000)}
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