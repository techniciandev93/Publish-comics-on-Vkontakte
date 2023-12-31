import os
import random
from urllib.parse import urlparse
import requests
from dotenv import load_dotenv


def check_vk_api_error(response):
    if response.get('error'):
        raise requests.HTTPError(response.get('error'))


def get_current_comics_number():
    current_comics_url = 'https://xkcd.com/info.0.json'
    response = requests.get(current_comics_url)
    response.raise_for_status()
    last_comics_number = response.json()['num']
    return last_comics_number


def get_random_comic(last_comics_number):
    random_number = random.randint(1, last_comics_number)
    comics_url = f'https://xkcd.com/{random_number}/info.0.json'
    response_comics = requests.get(comics_url)
    response_comics.raise_for_status()
    information_comic = response_comics.json()
    comics_img_url = information_comic['img']
    comics_comment = information_comic['alt']
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


def upload_image_vk(file_path, access_token, api_version, group_id):
    params = {'access_token': access_token, 'v': api_version, 'group_id': group_id}
    vk_upload_image_url = 'https://api.vk.com/method/photos.getWallUploadServer'
    save_image_vk_url = 'https://api.vk.com/method/photos.saveWallPhoto'
    response = requests.get(vk_upload_image_url, params=params)
    response.raise_for_status()
    response_vk = response.json()
    check_vk_api_error(response_vk)
    upload_url = response_vk['response']['upload_url']

    with open(file_path, 'rb') as file:
        upload_response = requests.post(upload_url, files={'photo': file})
    upload_response.raise_for_status()
    check_vk_api_error(upload_response.json())

    params.update(upload_response.json())
    img_response = requests.post(save_image_vk_url, params=params)
    img_response.raise_for_status()
    information_img = img_response.json()
    check_vk_api_error(information_img)
    image_url = information_img['response'][0]['sizes'][-1]['url']
    owner_id = information_img['response'][0]['owner_id']
    media_id = information_img['response'][0]['id']
    return image_url, owner_id, media_id


def publish_vk_post(image_url, owner_id, media_id, group_id, api_version, access_token, message):
    publish_entry_vk_url = 'https://api.vk.com/method/wall.post'
    params = {
        'owner_id': f'-{group_id}',
        'v': api_version,
        'access_token': access_token,
        'attachments': f'photo{owner_id}_{media_id},{image_url}',
        'message': message
    }
    response = requests.post(publish_entry_vk_url, params=params)
    check_vk_api_error(response.json())
    response.raise_for_status()


if __name__ == '__main__':
    comics_file_name = ''
    try:
        load_dotenv()
        vk_access_token = os.environ['VK_ACCESS_TOKEN']
        vk_group_id = os.environ['VK_GROUP_ID']
        api_vk_version = 5.154

        current_comics_number = get_current_comics_number()
        comics_file_name, comics_vk_comment = get_random_comic(current_comics_number)
        image_vk_url, owner_vk_id, media_vk_id = upload_image_vk(comics_file_name, vk_access_token, api_vk_version,
                                                                 vk_group_id)
        publish_vk_post(image_vk_url, owner_vk_id, media_vk_id, vk_group_id, api_vk_version, vk_access_token,
                        comics_vk_comment)
    finally:
        if os.path.exists(comics_file_name):
            os.remove(comics_file_name)
