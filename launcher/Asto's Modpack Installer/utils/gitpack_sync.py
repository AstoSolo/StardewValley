import zipfile
import shutil
from pathlib import Path
import requests
from utils import logger

def download_config_zip(url: str, output_path: Path):
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()

        with open(output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        logger.log(f"Загружен архив конфигураций: {output_path.name}")

    except Exception as e:
        logger.log(f"Ошибка при загрузке архива конфигураций: {e}")
        raise

def extract_config_zip(zip_path: Path, extract_to: Path):
    try:
        if extract_to.exists():
            shutil.rmtree(extract_to)
        extract_to.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(extract_to)

        logger.log(f"Распакован архив конфигураций в: {extract_to}")

    except Exception as e:
        logger.log(f"Ошибка при распаковке архива конфигураций: {e}")
        raise

def apply_configs(source_dir: Path, overwrite_dest: Path, profiles_dest: Path):
    try:
        # overwrite
        source_overwrite = source_dir / "overwrite"
        if source_overwrite.exists():
            if overwrite_dest.exists():
                shutil.rmtree(overwrite_dest)
            shutil.copytree(source_overwrite, overwrite_dest)
            logger.log(f"overwrite скопирован в: {overwrite_dest}")
        else:
            logger.log("Папка overwrite не найдена в архиве")

        # profiles
        source_profiles = source_dir / "profiles"
        if source_profiles.exists():
            if profiles_dest.exists():
                shutil.rmtree(profiles_dest)
            shutil.copytree(source_profiles, profiles_dest)
            logger.log(f"profiles скопирован в: {profiles_dest}")
        else:
            logger.log("Папка profiles не найдена в архиве")

    except Exception as e:
        logger.log(f"Ошибка при применении конфигураций: {e}")
        raise