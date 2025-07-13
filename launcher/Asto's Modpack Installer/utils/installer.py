import zipfile, shutil
from pathlib import Path
from utils import logger

def extract_zip(zip_path: Path, extract_to: Path):
    """Распаковывает ZIP-архив в указанную папку."""
    with zipfile.ZipFile(zip_path, "r") as archive:
        archive.extractall(extract_to)
    logger.log(f"Распакован: {zip_path.name}")

def create_meta_ini(mod_name: str, mods_dir: Path, version: str = "1.0"):
    """Создаёт минимальный meta.ini для мода."""
    dest_dir = mods_dir / mod_name
    meta_path = dest_dir / "meta.ini"

    content = f"""[General]
gameName=stardewvalley
version={version}
repository=Local
"""
    with open(meta_path, "w", encoding="utf-8") as file:
        file.write(content)

    logger.log(f"Создан meta.ini для мода: {mod_name}")


def clean_cache(cache_dir):
    """Удаляет содержимое папки кэша."""
    if cache_dir.exists() and cache_dir.is_dir():
        shutil.rmtree(cache_dir)
        logger.log(f"Очищен кэш: {cache_dir}")
    else:
        logger.log(f"Кэш не найден или уже пуст: {cache_dir}")