from PIL import Image, ImageFont, ImageDraw 
import requests
import io

# ------------------
# Global constants
# ---
# Textbox constants
UPPER_BOXES_START_POINT = (50, 100)
UPPER_BOXES_WIDTH = 550
UPPER_SECTIONS = ["title", "description"]

LOWER_BOXES_START_POINT = (50, 750)
LOWER_BOXES_WIDTH = 500
LOWER_SECTIONS = ["date", "time", "location", "cost"]
LOWER_SECTIONS_ORDER = {"date":1,
                         "time":2, 
                         "location":3,
                         "cost":4} # Defines the order of each box. If one section is not present, the next one will take its place
BOX_MARGIN = 8
CONTACTS_BOX_START_POINT = (130,1000)
# ---
# Text color constants
TEXT_COLOR = (255,255,255)
STROKE_WIDTH = 2
STROKE_COLOR = (0,0,0)
# Text size constants
CONTACT_TEXT_SIZE = 30
# Font constants
TEXT_FONT = "montserratalternates/MontserratAlternates-Bold.ttf"
CONTACT_FONT = "montserratalternates/MontserratAlternates-Bold.ttf"
# ---
# Icons constants
ICONS_PATH = "../../images/icons/"
ICONS_DICT = {"date":"calendar-color.png", 
              "time":"clock-color.png", 
              "location":"map2-color.png", 
              "cost":"cash-color.png"}
# ---
# Contacts constants
CONTACTS = {
    "email": {"text": "ludusgate@gmail.com",
                "icon":"email-color.png"},
    "whatsapp": {"text": "34X XXX XX XX",
                "icon":"whatsapp-logo-color.png"},
    "insta_dm": {"text": "DM: @ludusgate",
                "icon":"instagram-color.png"}
}

# ------------------

def draw_textboxes(my_image, edit_dict):
    """
    Disegno i rettangoli dei textboxes sull'immagine. 
    Necessaria solo per la fase di sviluppo, non usata in produzione.
    """
    image_editable = ImageDraw.Draw(my_image)

    upper_y_0 = UPPER_BOXES_START_POINT[1]
    lower_y_0 = LOWER_BOXES_START_POINT[1]

    for scope in edit_dict.keys():
        if edit_dict[scope]["text"] != "":
            if scope in UPPER_SECTIONS:
                upper_textbox = ((UPPER_BOXES_START_POINT[0], UPPER_BOXES_START_POINT[1]), 
                                 (UPPER_BOXES_START_POINT[0]+UPPER_BOXES_WIDTH, upper_y_0+edit_dict[scope]["size"]))
                image_editable.rectangle(upper_textbox, width=3)
                upper_y_0 = upper_y_0+edit_dict[scope]["size"]
            else: 

                lower_textbox = ((LOWER_BOXES_START_POINT[0], LOWER_BOXES_START_POINT[1]), 
                                 (LOWER_BOXES_START_POINT[0]+LOWER_BOXES_WIDTH, lower_y_0+edit_dict[scope]["size"]))
                image_editable.rectangle(lower_textbox, width=3)
                lower_y_0 = lower_y_0+edit_dict[scope]["size"]
    return my_image

def get_google_font(font: str, size=24):
    # MIGLIORIA: SCARICARE IL FONT SOLO UNA VOLTA E TENERLO BUONO PER TUTTE LE SEZIONI
    # E' POSSIBILE? FORSE NO PERCHé VA SCARICATO PER LA SIZE SPECIFICA DI QUEL TESTO
    """
    Questa funzione scarica temporaneamente da github.com/google/fonts/ il file .ttf del font desiderato.
    font: stringa indicante il percorso del font su github.com/google/fonts/ nel formato cartella/font_file.ttf
    size: dimensione del font
    """
    url = f"https://github.com/google/fonts/blob/main/ofl/{font}?raw=true"
    r = requests.get(url, allow_redirects=True)
    font = ImageFont.truetype(io.BytesIO(r.content), size=size)

    return font

def crop_image(my_image, aspect_ratio: tuple):
    """
    Ritaglia l'immagine di input secondo le dimensioni desiderate. L'immagine viene sempre ritagliata centralmente.
    my_image: immagine da croppare
    aspect_ratio: dimensione finale dell'immagine in pixels
    """
    image  = my_image
    width  = image.size[0]
    height = image.size[1]

    aspect_now = width / float(height)

    ideal_width = aspect_ratio[0]
    ideal_height = aspect_ratio[1]
    ideal_aspect = ideal_width / float(ideal_height)

    if aspect_now > ideal_aspect:
        # Then crop the left and right edges:
        new_width = int(ideal_aspect * height)
        offset = (width - new_width) / 2
        resize = (offset, 0, width - offset, height)
    else:
        # ... crop the top and bottom:
        new_height = int(width / ideal_aspect)
        offset = (height - new_height) / 2
        resize = (0, offset, width, height - offset)

    image = image.crop(resize).resize((ideal_width, ideal_height), Image.LANCZOS)
    return image

def get_text_size(max_width, text, font, max_size):
    """
    Ottenere il font size appropriato per farci stare il testo nella box in una singola linea
    """

    # Get appropriate font size to make the text fit the box in a single line
    max_size = max_size # Start from default font size
    text_length = get_google_font(font, max_size).getlength(text) # Get text length given font and size
    # Finché il testo non ci sta nel box predefinito, riduco la size di 2 punti e riprovo
    while text_length > max_width:
        max_size -= 2
        text_length = get_google_font(font, max_size).getlength(text)
    actual_size = max_size
    
    return actual_size

def get_text_position(textbox, anchor):
    """
    Dato il textbox entro cui deve essere scritto il testo, e il tipo di anchor (i.e. posizione del testo rispetto alla textbox),
    ritorna la posizione da cui deve essere scritto il testo
        - se testo centrato ("anchor" == "mm"): posizione = centro del box
        - se testo allineato a dx ("anchor" == "lb"): posizione = angolo lower left del box
        - se testo allineato a dx ("anchor" == "lm"): posizione = middle left del box
        - per ora ci sono solo queste casistiche    
    """
    # Get textbox hight from coordinates
    box_h = textbox[1][1] - textbox[0][1]

    # Determinare la posizione del testo  
    if anchor == "mm":
        position_x = (textbox[1][0]+textbox[0][0])/2
        position_y = (textbox[1][1]+textbox[0][1])/2
    elif anchor == "lb":
        position_x = textbox[0][0]
        position_y = textbox[0][1] + box_h
    elif anchor == "lm":
        position_x = textbox[0][0]
        position_y = textbox[0][1] + box_h/2

    return (int(position_x), int(position_y))

def write_contacts(my_image):
    image_editable = ImageDraw.Draw(my_image)

    writing_cursor_y = CONTACTS_BOX_START_POINT[1]
    for contact in CONTACTS.keys():
        writing_cursor_x = CONTACTS_BOX_START_POINT[0]
        # Get icon
        icon_path = ICONS_PATH+CONTACTS[contact]["icon"]
        icon = Image.open(icon_path)
        # Resize icon
        icon.thumbnail((CONTACT_TEXT_SIZE, CONTACT_TEXT_SIZE), Image.Resampling.LANCZOS)
        # Paste the icon on the image
        icon_position = (int(writing_cursor_x), int(writing_cursor_y))
        my_image.paste(icon, icon_position, mask=icon)
        writing_cursor_x += CONTACT_TEXT_SIZE+BOX_MARGIN 

        # Write the text
        text = CONTACTS[contact]["text"]
        text_position = (int(writing_cursor_x), int(writing_cursor_y))
        image_editable.text(text_position, 
                            text,                        
                            TEXT_COLOR,
                            font=get_google_font(CONTACT_FONT, CONTACT_TEXT_SIZE),
                            stroke_width=STROKE_WIDTH,
                            stroke_fill=STROKE_COLOR)
        writing_cursor_y += CONTACT_TEXT_SIZE+BOX_MARGIN

    return my_image

def write_on_image(my_image, edit_dict):
    """
    Prende in input una PIL.Image e la rende editabile.
    Itera fra le sezioni di testo (scope) presenti in edit_dict. 

    https://pillow.readthedocs.io/en/stable/handbook/text-anchors.html
    """
    image_editable = ImageDraw.Draw(my_image)

    upper_y_0 = UPPER_BOXES_START_POINT[1]
    lower_y_0 = LOWER_BOXES_START_POINT[1]

    for scope in edit_dict.keys():
        if edit_dict[scope]["text"] != "": # Solo se la sezione contiene del testo (NB: migliorare la gestione delle sezioni senza testo)
            if scope in UPPER_SECTIONS:
                # Calcolo dimensione carattere adeguata in base al testo e alla larghezza del box
                actual_size = get_text_size(UPPER_BOXES_WIDTH, edit_dict[scope]["text"], TEXT_FONT, edit_dict[scope]["size"])
                # Definisco le coordinate del textbox in base a dove siamo arrivati a scrivere e alla dimensione del carattere
                upper_textbox = ((UPPER_BOXES_START_POINT[0], upper_y_0), 
                                 (UPPER_BOXES_START_POINT[0]+UPPER_BOXES_WIDTH, upper_y_0+actual_size)) 
                # Calcolo la posizione di scrittura del testo
                position = get_text_position(upper_textbox, edit_dict[scope]["anchor"])
                # Scrivo il testo
                image_editable.text(position, 
                                    edit_dict[scope]["text"],
                                    TEXT_COLOR,
                                    anchor=edit_dict[scope]["anchor"],
                                    font=get_google_font(TEXT_FONT
                                                            , actual_size),
                                    stroke_width=STROKE_WIDTH,
                                    stroke_fill=STROKE_COLOR)
                # Effettuo update delle coordinate del prossimo upper textbox
                upper_y_0 = upper_y_0+actual_size+BOX_MARGIN

            elif scope in LOWER_SECTIONS:
                # Calcolo dimensione carattere adeguata in base al testo e alla larghezza del box
                actual_size = get_text_size(LOWER_BOXES_WIDTH, edit_dict[scope]["text"], TEXT_FONT, edit_dict[scope]["size"])
                 # Definisco le coordinate del textbox in base a dove siamo arrivati a scrivere e alla dimensione del carattere 
                lower_textbox = ((LOWER_BOXES_START_POINT[0], lower_y_0), 
                                 (LOWER_BOXES_START_POINT[0]+LOWER_BOXES_WIDTH, lower_y_0+actual_size))
                # Calcolo la posizione di scrittura del testo
                position = get_text_position(lower_textbox, edit_dict[scope]["anchor"])   
                # Scrivo il testo
                image_editable.text(position, 
                                    edit_dict[scope]["text"],
                                    TEXT_COLOR,
                                    anchor=edit_dict[scope]["anchor"],
                                    font=get_google_font(TEXT_FONT
                                                            , actual_size),
                                    stroke_width=STROKE_WIDTH,
                                    stroke_fill=STROKE_COLOR)
                
                # If I have an icon for this section, I add it
                if scope in ICONS_DICT.keys():                    
                    # Get icon
                    icon_path = ICONS_PATH+ICONS_DICT[scope]
                    icon = Image.open(icon_path)
                    # Resize icon
                    icon.thumbnail((actual_size, actual_size), Image.Resampling.LANCZOS)

                    # Paste icon on poster
                    icon_position = (position[0]-actual_size-3, position[1]-int(actual_size/2)) # 3 è un ulteriore offset renderlo parametrico ??
                    # Paste the icon on the image
                    my_image.paste(icon, icon_position, mask=icon)
                
                # Effettuo update delle coordinate del prossimo lower textbox
                lower_y_0 = lower_y_0+actual_size+BOX_MARGIN
    
    my_image = write_contacts(my_image)


    return my_image

def image_edit(img_path: str, edit_dict: dict, crop=True, textboxes=False):
    """
    Funzione principale per l'editing dell'immagine. Richiama la funzione di cropping e di writing.
    Le logiche sul posizionamento del testo sono richiamate da write_on_image().
    Viene salvata fisicamente l'immagine di output con il prefisso "EDIT_".
    """    
    if crop:
        # Carico immagine
        my_image = Image.open(img_path) 
        # Crop immagine
        my_image = crop_image(my_image, (648,1152))
    else:
        # Carico immagine
        my_image = Image.open(img_path) 

    my_image = write_on_image(my_image, edit_dict)

    # Richiamo della funzione per disegnare i textboxes. Disattivata di default.
    if textboxes:
        my_image = draw_textboxes(my_image, edit_dict)

    # Salvataggio risutlato
    output_path = "EDIT_"+img_path
    my_image.save(output_path)
    
    return output_path

