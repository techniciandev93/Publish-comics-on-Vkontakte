import os
import random
from urllib.parse import urlparse
import requests
from dotenv import load_dotenv


def get_number_current_comics(url):
    response = requests.get(url)
    response.raise_for_status()
    last_comics_number = response.json()['num']
    return last_comics_number


def get_random_comics(last_comics_number):
    random_number = random.randint(1, last_comics_number)
    comics_url = f'https://xkcd.com/{random_number}/info.0.json'
    response_comics = requests.get(comics_url)
    response_comics.raise_for_status()
    comics_img_url = response_comics.json()['img']
    comics_comment = response_comics.json()['alt']
    file_name = save_img_file(comics_img_url)
    return file_name, comics_comment


def save_img_file(url):
    response = requests.get(url)
    response.raise_for_status()
    parse_url = urlparse(url)
    file_name = os.path.basename(parse_url.path)
    with open(file_name, 'wb') as file:
        file.write(response.content)
    return file_name


def upload_image_vk(upload_img_url, save_img_url, file_path,  params):
    response = requests.get(upload_img_url, params=params)
    response.raise_for_status()
    upload_url = response.json()['response']['upload_url']

    with open(file_path, 'rb') as file:
        upload_response = requests.post(upload_url, files={'photo': file})
        upload_response.raise_for_status()

    params.update(upload_response.json())
    img_response = requests.post(save_img_url, params=params)
    img_response.raise_for_status()

    image_url = img_response.json()['response'][0]['sizes'][-1]['url']
    owner_id = img_response.json()['response'][0]['owner_id']
    media_id = img_response.json()['response'][0]['id']
    return image_url, owner_id, media_id


def publish_vk_post(publish_entry_url, image_url, owner_id, media_id, group_id, api_version, access_token, message):
    params = {
        'owner_id': f'-{group_id}',
        'v': api_version,
        'access_token': access_token,
        'attachments': f'photo{owner_id}_{media_id},{image_url}',
        'message': message
    }
    response = requests.post(publish_entry_url, params=params)
    response.raise_for_status()


if __name__ == '__main__':
    load_dotenv()
    vk_access_token = os.environ['VK_ACCESS_TOKEN']
    vk_group_id = os.environ['VK_GROUP_ID']
    api_vk_version = 5.154

    vk_params = {'access_token': vk_access_token, 'v': api_vk_version, 'group_id': vk_group_id}

    vk_upload_image_url = 'https://api.vk.com/method/photos.getWallUploadServer'
    save_image_vk_url = 'https://api.vk.com/method/photos.saveWallPhoto'
    publish_entry_vk_url = 'https://api.vk.com/method/wall.post'
    current_comics_url = 'https://xkcd.com/info.0.json'

    current_comics_number = get_number_current_comics(current_comics_url)
    comics_file_name, comics_vk_comment = get_random_comics(current_comics_number)

    image_vk_url, owner_vk_id, media_vk_id = upload_image_vk(vk_upload_image_url, save_image_vk_url, comics_file_name,
                                                             vk_params)

    publish_vk_post(publish_entry_vk_url, image_vk_url, owner_vk_id, media_vk_id, vk_group_id, api_vk_version,
                    vk_access_token,
                    comics_vk_comment)
    os.remove(comics_file_name)
