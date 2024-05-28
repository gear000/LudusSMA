import json
import requests # type: ignore
import base64

def load_imgur(imgur_config, img_path):
    """
    Uploads an image to Imgur using the provided Imgur configuration and image path.

    Parameters:
        imgur_config (dict): A dictionary containing the Imgur configuration, including the Imgur client ID.
        img_path (str): The path to the image file to be uploaded.

    Returns:
        str: The URL of the uploaded image on Imgur.

    Raises:
        Exception: If the image upload fails with a status code other than 200.
    """

    # Set API endpoint and headers
    url = "https://api.imgur.com/3/image"

    headers = {
        'Authorization': f"Client-ID {imgur_config['imgur_client_id']}",
    }
    params = {
        'image': base64.b64encode(open(img_path, 'rb').read())
    }

    r = requests.post(url, headers=headers, data=params)
    if r.status_code != 200:
        raise Exception("E04: Upload immagine fallito.")
    # print('status:', r.status_code)
    data = r.json()
    
    return data["data"]["link"]