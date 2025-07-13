import requests
from pathlib import Path
from utils import logger

def download_file(url: str, dest_path: Path):
    """Скачивает файл по URL и сохраняет его в dest_path."""
    response = requests.get(url)
    response.raise_for_status()
    with open(dest_path, "wb") as file:
        file.write(response.content)
    logger.log(f"Скачан: {dest_path.name}")
