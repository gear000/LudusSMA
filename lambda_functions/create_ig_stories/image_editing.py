from PIL import Image, ImageFont, ImageDraw 
import requests
import io

UPPER_BOXES_START_POINT = (50, 50)
UPPER_BOXES_WIDTH = 550
UPPER_SECTIONS = ["title", "body"]

LOWER_BOXES_START_POINT = (50, 860)
LOWER_BOXES_WIDTH = 500
LOWER_SECTIONS = ["date", "time", "location", "cost"]

BOX_MARGIN = 5

def draw_textboxes(my_image, edit_dict):
    """
    Disegno i rettangoli dei textboxes sull'immagine. 
    Necessaria solo per la fase di sviluppo, non usata in produzione.
    """

    image_editable = ImageDraw.Draw(my_image)

    # x_0 = 50
    # y_0 = 860
    # x_1 = 524
    # y_1 = 524
    # lower_textbox = ((50, 860), (524,))
    upper_y_0 = UPPER_BOXES_START_POINT[1]
    lower_y_0 = LOWER_BOXES_START_POINT[1]

    for scope in edit_dict.keys():
        if edit_dict[scope]["text"] != "":
            if scope in ["title", "body"]:
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
    # img_path_cropped = "CROPPED_"+img_path
    # thumb.save(img_path_cropped)
    return image

def get_text_size(max_width, text, font, max_size):
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
    # Get textbox dimensions from coordinates
    box_h = textbox[1][1] - textbox[0][1]

    # Determinare la posizione del testo
    # - se testo centrato ("anchor" == "mm"): posizione = centro del box
    # - se testo allineato a dx ("anchor" == "lb"): posizione = angolo lower left del box
    # - se testo allineato a dx ("anchor" == "lm"): posizione = middle left del box
    # - per ora ci sono solo queste casistiche
        
    if anchor == "mm":
        position_x = (textbox[1][0]+textbox[0][0])/2
        position_y = (textbox[1][1]+textbox[0][1])/2
        position = (position_x, position_y)
    elif anchor == "lb":
        position_x = textbox[0][0]
        position_y = textbox[0][1] + box_h
        position = (position_x, position_y)
    elif anchor == "lm":
        position_x = textbox[0][0]
        position_y = textbox[0][1] + box_h/2
        position = (position_x, position_y)

    return position

def write_on_image(my_image, edit_dict):
    """
    https://pillow.readthedocs.io/en/stable/handbook/text-anchors.html
    """

    image_editable = ImageDraw.Draw(my_image)


    upper_y_0 = UPPER_BOXES_START_POINT[1]
    lower_y_0 = LOWER_BOXES_START_POINT[1]

    for scope in edit_dict.keys():
        if edit_dict[scope]["text"] != "":
            if scope in UPPER_SECTIONS:
                actual_size = get_text_size(UPPER_BOXES_WIDTH, edit_dict[scope]["text"], edit_dict[scope]["font"], edit_dict[scope]["size"])
                upper_textbox = ((UPPER_BOXES_START_POINT[0], upper_y_0), 
                                 (UPPER_BOXES_START_POINT[0]+UPPER_BOXES_WIDTH, upper_y_0+actual_size)) 
                position = get_text_position(upper_textbox, edit_dict[scope]["anchor"])      

                # print(actual_size)        
                image_editable.text(position, 
                                    edit_dict[scope]["text"],
                                    edit_dict[scope]["color"],
                                    anchor=edit_dict[scope]["anchor"],
                                    font=get_google_font(edit_dict[scope]["font"]
                                                            , actual_size))
                upper_y_0 = upper_y_0+actual_size+BOX_MARGIN
                # print(scope, upper_y_0)
            elif scope in LOWER_SECTIONS:
                # print(scope)
                actual_size = get_text_size(LOWER_BOXES_WIDTH, edit_dict[scope]["text"], edit_dict[scope]["font"], edit_dict[scope]["size"])
                # print("actual_size", actual_size)  
                lower_textbox = ((LOWER_BOXES_START_POINT[0], lower_y_0), 
                                 (LOWER_BOXES_START_POINT[0]+LOWER_BOXES_WIDTH, lower_y_0+actual_size))
                # print(lower_textbox)
                position = get_text_position(lower_textbox, edit_dict[scope]["anchor"])   

                      
                # print("position", position)   
                # image_editable.rectangle(lower_textbox, width=3)
                image_editable.text(position, 
                                    edit_dict[scope]["text"],
                                    edit_dict[scope]["color"],
                                    anchor=edit_dict[scope]["anchor"],
                                    font=get_google_font(edit_dict[scope]["font"]
                                                            , actual_size))
                lower_y_0 = lower_y_0+actual_size+BOX_MARGIN
    
    return my_image

def image_edit(img_path: str, edit_dict: dict, crop=True):
    
    if crop:
        # Carico immagine
        my_image = Image.open(img_path) 
        # Crop immagine
        my_image = crop_image(my_image, (648,1152))
    else:
        # Carico immagine
        my_image = Image.open(img_path) 

    my_image = write_on_image(my_image, edit_dict)
    # my_image = draw_textboxes(my_image, edit_dict)

    # Salvataggio risutlato
    my_image.save("EDIT_"+img_path)

