import modio
import json
import os
from packaging.version import parse
import requests
import zipfile

CONFIG_PATH = './config.json'
CACHE_PATH = './cache/'
MODS_PATH = './mods/'

def create_new_config():
    with open(CONFIG_PATH, 'w') as config_file:
        config_file.write(
            json.dumps(
                {
                    "api_key": 'api_key',
                    "oauth2": 'oauth2',
                    "game": 'game',
                },
                indent=4
            )
        )


def get_new_client():
    api_key = input('Please enter your API key.\n>: ')
    client = modio.Client(api_key=api_key)
    client.email_request(input('Please enter Mod.IO Email Address. (A security code will be emailed for authentication)\n>: '))
    oauth2 = client.email_exchange(input('Please enter the emailed security code. \n>: '))
    return api_key, oauth2, client


def read_config_file():
    with open(CONFIG_PATH, 'r') as config_file:
        return json.loads(config_file.read())


def write_config_file(config_dict):
    with open(CONFIG_PATH, 'w') as config_file:
        config_file.write(json.dumps(config_dict, indent=4))


def get_or_create_client_config():
    if not os.path.exists(CONFIG_PATH):
        create_new_config()
    config_dict = read_config_file()
    if "api_key" not in config_dict or "oauth2" not in config_dict:
        api_key, oauth2, client = get_new_client()
        config_dict["api_key"] = api_key
        config_dict["oauth2"] = oauth2
        write_config_file(config_dict)
    if "game" not in config_dict:
        game = input('Please enter the name of desired Mod.IO game.\n>: ')
        config_dict["game"] = game
        write_config_file(config_dict)
    if 'client' not in locals():
        client = modio.Client(api_key=config_dict["api_key"], access_token=config_dict["oauth2"])
    return config_dict, client


def get_subbed_mods():
    config, client = get_or_create_client_config()
    gameid = client.get_games(filters=modio.Filter({'name': config["game"]})).results[0].id
    return client.get_my_subs(filters=modio.Filter({'game_id': gameid})).results


def get_highest_file_url(mod):
    files = mod.get_files().results
    url_selected = ''
    highest_version = parse("0.0.0")
    for file in files:
        version_string = file.version
        if version_string is None:
            version_string = "0.0.0"
        version = parse(version_string)
        if version > highest_version:
            highest_version = version
            url_selected = file.url
    return url_selected


def get_newest_mod_urls(mods):
    return [get_highest_file_url(mod) for mod in mods]


def download_file(url):
    response = requests.get(url)
    if "content-disposition" in response.headers:
        content_disposition = response.headers["content-disposition"]
        filename = content_disposition.split("filename=")[1]
    else:
        filename = response.url.split("/")[-1].split("?")[0]
    with open(CACHE_PATH+filename, mode="wb") as file:
        file.write(response.content)
    print(f"Downloaded file {filename}")


def update_subbed_mods():
    mods = get_subbed_mods()
    urls_to_process = get_newest_mod_urls(mods)
    for url in urls_to_process:
        download_file(url)


def extract_mods():
    for item in os.listdir(CACHE_PATH):
        if item.endswith(".zip"):
            with zipfile.ZipFile(os.path.abspath(CACHE_PATH+item)) as zip_ref:
                zip_ref.extractall(MODS_PATH)

# update_subbed_mods()
extract_mods()
