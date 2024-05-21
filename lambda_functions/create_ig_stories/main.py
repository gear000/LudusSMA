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
    # https://stackoverflow.com/questions/1970807/center-middle-align-text-with-pil
    # https://pillow.readthedocs.io/en/stable/handbook/text-anchors.html
    # - scegliere colore testo parametrico, adatto all'immagine
    # - aggiungere icone per luogo, data, ora, costo etc. e metterle a sx del testo
    # - mettere che se il "text" è vuoto skippare quel box e passare al successivo
    #   per i box piccoli sotto (data, ora, luogo, costo,...) partire sempre dalla data che ci deve essere sempre e per cui ho le coordinate fissate del box,
    #   poi per i seguenti se i text sono != da "" aggiungo il box e ne calcolo in modo parametrico le coordinate

    edit_dict = {
        "title": {"text": "Torneo di Bang",
                  "font": "montserratalternates/MontserratAlternates-Bold.ttf",
                  "size": 90, 
                  "color": (255, 255, 255),
                #   "position":(324,100),
                  "textbox":((50, 30), (600, 170)),
                  "anchor":"mm"},
        "body": {"text": "",
                  "font": "montserratalternates/MontserratAlternates-Bold.ttf",
                  "size": 80, 
                  "color": (255, 255, 255),
                #   "position":(0,0),
                  "textbox":((50, 170), (600, 270)),
                  "anchor":"mm"},        
        "date": {"text": "Mercoledì 31 febbraio",
                  "font": "montserratalternates/MontserratAlternates-Bold.ttf",
                  "size": 40, 
                  "color": (255, 255, 255),
                #   "position":(0,950),
                  "textbox":((50, 860), (524, 900)),
                  "anchor":"lm"},
        "time": {"text": "21:00",
                  "font": "montserratalternates/MontserratAlternates-Bold.ttf",
                  "size": 40, 
                  "color": (255, 255, 255),
                #   "position":(0,950),
                  "textbox":((50, 900), (524, 940)),
                  "anchor":"lm"},
        "location": {"text": "Centro NOI di Povegliano",
                  "font": "montserratalternates/MontserratAlternates-Bold.ttf",
                  "size": 40, 
                  "color": (255, 255, 255),
                #   "position":(0,900),
                  "textbox":((50, 940), (524, 980)),
                  "anchor":"lm"},
        "cost": {"text": "Iscrizione libera",
                  "font": "montserratalternates/MontserratAlternates-Bold.ttf",
                  "size": 40, 
                  "color": (255, 255, 255),
                #   "position":(0,1000),
                  "textbox":((50, 980), (524, 1020)),
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