import argparse
import hashlib
import sys
import tarfile
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory

from backup_config import CONFIG_PATH, load_config, resolve_path
from config_menu import run_config_menu


def create_backup(config_path):
    config = load_config(config_path)
    if not config["sources"]:
        raise ValueError("A sources mezőben adj meg legalább egy mappát.")

    sources = [resolve_path(config_path, source) for source in config["sources"]]
    destination = resolve_path(config_path, config.get("destination"))
    for source in sources:
        if not source.is_dir():
            raise ValueError(f"A forrásmappa nem található: {source}")
        if destination.is_relative_to(source):
            raise ValueError(f"A mentés célja nem lehet a forrásmappán belül: {source}")

    destination.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    backup_path = destination / timestamp
    if backup_path.exists():
        raise ValueError(f"Ebben a percben már készült mentés: {backup_path}")

    with TemporaryDirectory(prefix=f"folyamatban-{timestamp}-", dir=destination) as temporary:
        staging = Path(temporary)
        archive = staging / f"backup_{timestamp}.tar.gz"
        with tarfile.open(archive, "w:gz") as tar:
            for index, source in enumerate(sources, start=1):
                tar.add(source, arcname=f"{index:02d}-{source.name}")

        checksum = hashlib.sha256()
        with archive.open("rb") as archive_file:
            for chunk in iter(lambda: archive_file.read(1024 * 1024), b""):
                checksum.update(chunk)
        archive.with_suffix(".gz.sha256").write_text(
            f"{checksum.hexdigest()}  {archive.name}\n", encoding="ascii"
        )
        staging.rename(backup_path)

    return backup_path


def main():
    parser = argparse.ArgumentParser(description="Mappák mentése tömörített archívumba.")
    parser.add_argument(
        "--config", action="store_true", help="A mentendő mappák kezelése."
    )
    args = parser.parse_args()
    if args.config:
        try:
            run_config_menu(CONFIG_PATH)
        except FileNotFoundError:
            sys.exit("Másold a config.example.json fájlt config.json néven.")
        except (OSError, ValueError, RuntimeError) as error:
            sys.exit(f"Konfigurációs hiba: {error}")
        return

    try:
        print(f"Mentés elkészült: {create_backup(CONFIG_PATH)}")
    except (OSError, ValueError, RuntimeError, tarfile.TarError) as error:
        sys.exit(f"Mentési hiba: {error}")


if __name__ == "__main__":
    main()
