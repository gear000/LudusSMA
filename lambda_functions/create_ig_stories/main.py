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


    # edit_dict = {
    #     "title": {"text": "Torneo di Bang",
    #               "font": "ARCADECLASSIC.TTF",
    #               "size": 150, 
    #               "color": (55, 0, 134),
    #               "position":},
    #     "body": {"text": "",
    #               "font": "ARCADECLASSIC.TTF",
    #               "size": 80, 
    #               "color": (55, 0, 134),
    #               "position":},
    #     "location": {"text": "Centro NOI di Povegliano",
    #               "font": "ARCADECLASSIC.TTF",
    #               "size": 80, 
    #               "color": (55, 0, 134),
    #               "position":},
    #     "datetime": {"text": "Mercoledì 31 febbraio ore 21:00",
    #               "font": "ARCADECLASSIC.TTF",
    #               "size": 80, 
    #               "color": ,
    #               "position"},
    #     "cost": {"text": "Iscrizione libera",
    #               "font": "ARCADECLASSIC.TTF",
    #               "size": 80, 
    #               "color": (55, 0, 134),
    #               "position":}
    # }


    img_path_edit = image_edit(img_path, {})
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

    lambda_handler()