import zipfile, shutil
import subprocess
from typing import Optional
from pathlib import Path
from utils import logger

def extract_zip(zip_path: Path, extract_to: Path):
    """Распаковывает ZIP-архив в указанную папку."""
    with zipfile.ZipFile(zip_path, "r") as archive:
        archive.extractall(extract_to)
    logger.log(f"Распакован: {zip_path.name}")

def _extract_7z_with_py7zr(archive_path: Path, extract_to: Path) -> bool:
    try:
        import py7zr  # type: ignore
    except Exception:
        return False
    try:
        with py7zr.SevenZipFile(archive_path, mode='r') as z:
            z.extractall(path=extract_to)
        logger.log(f"Распакован (7z, py7zr): {archive_path.name}")
        return True
    except Exception as e:
        logger.error(f"py7zr не смог распаковать {archive_path.name}: {e}")
        return False

def _extract_7z_with_system(archive_path: Path, extract_to: Path) -> bool:
    # Требуется установленный 7z (пакет p7zip-full / p7zip)
    try:
        extract_to.mkdir(parents=True, exist_ok=True)
        result = subprocess.run(
            ["7z", "x", "-y", f"-o{str(extract_to)}", str(archive_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            logger.log(f"Распакован (7z, system): {archive_path.name}")
            return True
        logger.error(f"7z вернул код {result.returncode}: {result.stderr}")
        return False
    except FileNotFoundError:
        logger.error("Команда '7z' не найдена. Установите py7zr (python) или p7zip (system).")
        return False

def extract_archive(archive_path: Path, extract_to: Path):
    """Распаковывает архив (.zip, .7z) в указанную папку."""
    suffix = archive_path.suffix.lower()
    if suffix == ".zip":
        return extract_zip(archive_path, extract_to)
    if suffix == ".7z":
        # Сначала пытаемся py7zr, затем системный 7z
        if _extract_7z_with_py7zr(archive_path, extract_to):
            return
        if _extract_7z_with_system(archive_path, extract_to):
            return
        raise RuntimeError("Не удалось распаковать .7z архив: отсутствует py7zr и/или системный 7z")
    # Неизвестный формат
    raise ValueError(f"Неподдерживаемый формат архива: {suffix}")

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