from PIL import Image, ImageFont, ImageDraw 

def crop_image(img_path: str, aspect_ratio: tuple):
    image  = Image.open(img_path)
    width  = image.size[0]
    height = image.size[1]

    aspect_now = width / float(height)

    ideal_width = 648
    ideal_height = 1152
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

    thumb = image.crop(resize).resize((ideal_width, ideal_height), Image.ANTIALIAS)
    img_path_cropped = "CROPPED_"+img_path
    thumb.save(img_path_cropped)





def image_edit(img_path: str, edit_dict: dict, crop=True):

    if crop:
        # Crop immagine
        my_image = crop_image(img_path)
    else:
        # Carico immagine
        my_image = Image.open(img_path) 

    # # Carico parametri
    # title_text = edit_dict["title"]
    # # title_color = edit_dict["title_color"]
    # title_font =  edit_dict["title_font"]
    # # title_size = edit_dict["title_siz"]
    # body_text =  edit_dict["body"]
    # # body_color =  edit_dict["body_color"]
    # body_font = edit_dict["body_font"]
    # # body_size = edit_dict["body_s"]

    # image_editable = ImageDraw.Draw(my_image)
    # image_editable.text((15,15), body_text, (55, 0, 134), font=title_font)
    # image_editable.text((15,130), title_text, (55, 0, 134), font=title_font)



    return edited_path