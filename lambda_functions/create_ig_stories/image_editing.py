from PIL import Image, ImageFont, ImageDraw 
import requests
import io

def get_google_font(font: str, size=24):
    """
    Questa funzione scarica temporaneamente da github.com/google/fonts/ il file .ttf del font desiderato.
    font: stringa indicante il percorso del font su github.com/google/fonts/ nel formato cartella/font_file.ttf
    size: dimensione del font
    """
    url = f"https://github.com/google/fonts/blob/main/ofl/{font}?raw=true"
    print(url)
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

def write_on_image(my_image, edit_dict):
    image_editable = ImageDraw.Draw(my_image)

    for scope in edit_dict.keys():
        image_editable.text(edit_dict[scope]["position"], 
                            edit_dict[scope]["text"],
                            edit_dict[scope]["color"],
                            font=get_google_font(edit_dict[scope]["font"]
                                                    , edit_dict[scope]["size"]))
    
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

    # Salvataggio risutlato
    my_image.save("EDIT_"+img_path)

