import modio
import json
import os
from packaging.version import parse
import requests
import zipfile

CONFIG_PATH = './config.json'
CACHE_PATH = './cache/'
MODS_PATH = './mods/'


def create_default_config():
    default_config = {"api_key": 'api_key', "oauth2": 'oauth2', "game": 'game'}
    update_config(default_config)


def load_config():
    with open(CONFIG_PATH, 'r') as config_file:
        return json.loads(config_file.read())


def update_config(config_dict):
    with open(CONFIG_PATH, 'w') as config_file:
        config_file.write(json.dumps(config_dict, indent=4))


def get_or_create_client_config():
    if not os.path.exists(CONFIG_PATH):
        create_default_config()
    config_dict = load_config()
    if missing_keys := {"api_key", "oauth2", "game"} - config_dict.keys():
        if {"api_key", "oauth2"} & missing_keys:
            api_key = input('Please enter your API key.\n>: ')
            client = modio.Client(api_key=api_key)
            client.email_request(input('Please enter Mod.IO Email Address. (A security code will be emailed for authentication)\n>: '))
            oauth2 = client.email_exchange(input('Please enter the emailed security code. \n>: '))
            config_dict.update({"api_key": api_key, "oauth2": oauth2})
        if "game" in missing_keys:
            config_dict["game"] = input('Please enter the name of desired Mod.IO game.\n>: ')
        update_config(config_dict)
    client = modio.Client(api_key=config_dict["api_key"], access_token=config_dict["oauth2"])
    return config_dict, client


def get_highest_file_url(mod):
    highest_file = max(mod.get_files().results, key=lambda file: parse(file.version or "0.0.0"), default=None)
    return highest_file.url if highest_file else ''


def download_file(url):
    response = requests.get(url)
    filename = response.headers.get("content-disposition", "").split("filename=")[-1] or response.url.split("/")[-1].split("?")[0]
    with open(os.path.join(CACHE_PATH, filename), mode="wb") as file:
        file.write(response.content)
    print(f"Downloaded file {filename}")


def update_subbed_mods():
    config, client = get_or_create_client_config()
    gameid = client.get_games(filters=modio.Filter({'name': config["game"]})).results[0].id
    mods = client.get_my_subs(filters=modio.Filter({'game_id': gameid})).results
    urls_to_process = [get_highest_file_url(mod) for mod in mods]
    for url in urls_to_process:
        download_file(url)


def extract_mods():
    for item in os.listdir(CACHE_PATH):
        if item.endswith(".zip"):
            with zipfile.ZipFile(os.path.join(CACHE_PATH, item)) as zip_ref:
                zip_ref.extractall(MODS_PATH)


def main():
    update_subbed_mods()
    extract_mods()


main()
