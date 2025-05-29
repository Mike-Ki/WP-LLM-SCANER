import os
import shutil
import zipfile
from io import BytesIO
from typing import Any, List

import requests
from tqdm import tqdm

BASE_URL = "https://api.wordpress.org/plugins/info/1.2/"
DOWNLOAD_DIR = os.path.join('.', "downloaded_plugins")
PER_PAGE = 10  # Number of plugins per page


def fetch_plugin_names(page=1, per_page=PER_PAGE) -> Any | None:
    """Fetches plugins from the WordPress API."""
    url = f"{BASE_URL}?action=query_plugins&request[page]={page}&request[per_page]={per_page}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Failed to retrieve page {page}: {e}")
        return None


def _download_and_extract_plugin(slug, download_link, progress_bar):
    plugin_path = os.path.join(DOWNLOAD_DIR, slug)

    progress_bar.set_description(f"Downloading: {slug}")

    if os.path.exists(plugin_path):
        shutil.rmtree(plugin_path)

    try:
        response = requests.get(download_link, stream=True)
        response.raise_for_status()

        with zipfile.ZipFile(BytesIO(response.content)) as z:
            z.extractall(DOWNLOAD_DIR)
    except requests.RequestException as e:
        print(f"\nFailed to download {slug}: {e}")
    except zipfile.BadZipFile:
        print(f"\nFailed to extract {slug}: Not a valid zip file.")


def download_plugins(amount_of_plugins: int = None) -> None:
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    existing_plugins = [name for name in os.listdir(DOWNLOAD_DIR) if os.path.isdir(os.path.join(DOWNLOAD_DIR, name))]
    downloaded_count = len(existing_plugins)

    if amount_of_plugins is not None and downloaded_count >= amount_of_plugins:
        print(f"Already {downloaded_count} plugins downloaded. No more downloads needed.")
        return

    data = fetch_plugin_names(page=1)
    if not data or "info" not in data:
        print("Failed to retrieve the plugin information.")
        return

    total_pages = data["info"]["pages"]

    remaining_to_download = (
                amount_of_plugins - downloaded_count) if amount_of_plugins is not None else total_pages * PER_PAGE

    with tqdm(total=remaining_to_download, desc="Downloading plugins", unit="plugin") as progress_bar:
        for page in range(1, total_pages + 1):
            data = fetch_plugin_names(page=page)
            if not data or "plugins" not in data:
                continue

            for plugin in data["plugins"]:
                if amount_of_plugins is not None and downloaded_count >= amount_of_plugins:
                    return

                slug = plugin.get("slug")
                download_link = plugin.get("download_link")
                last_updated = plugin.get("last_updated")

                if not slug or not download_link or not last_updated:
                    continue

                plugin_path = os.path.join(DOWNLOAD_DIR, slug)

                if os.path.exists(plugin_path):
                    progress_bar.set_description(f"Already exists: {slug}")
                    progress_bar.update(1)
                    continue


def get_plugin_directories() -> List[str]:
    for root, dirs, files in os.walk(DOWNLOAD_DIR):
        dirs = [os.path.join(root, dir) for dir in dirs]
        dirs.sort()
        if dirs:
            return dirs
    return []


def get_code_base_as_dict(dir_name):
    code_base = {}
    code_base_dir = os.path.join(DOWNLOAD_DIR, dir_name)
    for root, dirs, files in os.walk(code_base_dir):
        for file in files:
            file_path = os.path.join(root, file)
            with open(file_path, 'rb') as f:
                code_base[file_path] = f.read()
    return code_base
