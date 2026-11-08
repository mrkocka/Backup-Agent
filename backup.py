import hashlib
import json
import sys
import tarfile
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory


def create_backup(config_path):
    config = json.loads(config_path.read_text(encoding="utf-8"))
    if not isinstance(config, dict):
        raise ValueError("A konfigurációnak JSON-objektumnak kell lennie.")

    sources = config.get("sources")
    destination = config.get("destination")
    if not isinstance(sources, list) or not sources:
        raise ValueError("A sources mezőben adj meg legalább egy mappát.")

    def resolve_path(value):
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Minden elérési út legyen nem üres szöveg.")
        return (config_path.parent / Path(value).expanduser()).resolve()

    sources = [resolve_path(source) for source in sources]
    destination = resolve_path(destination)
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

    with TemporaryDirectory(prefix=f".{timestamp}-", dir=destination) as temporary:
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


if __name__ == "__main__":
    try:
        config_path = Path(__file__).resolve().with_name("config.json")
        print(f"Mentés elkészült: {create_backup(config_path)}")
    except (OSError, ValueError, RuntimeError, tarfile.TarError) as error:
        sys.exit(f"Mentési hiba: {error}")
