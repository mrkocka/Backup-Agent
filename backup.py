import argparse
import hashlib
from time import perf_counter
from uuid import uuid4
import sys
import tarfile
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory

from backup_config import CONFIG_PATH, load_config, resolve_path
from config_menu import run_config_menu
from backup_reporting import open_log, finish_report, write_report, log_report


def create_backup(config_path):
    config_path = Path(config_path).resolve()
    started = perf_counter()
    report = {
        "started_at": datetime.now().astimezone().isoformat(),
        "archive_name": None,
        "archive_size_bytes": None,
    }
    config = load_config(config_path)
    log_path = resolve_path(config_path, config.get("log_file", "logs/backup.log"))
    logger = open_log(log_path)
    try:
        return build_backup(config_path, config, report, started, log_path)
    except (OSError, ValueError, RuntimeError, tarfile.TarError) as error:
        finish_report(report, started, error)
        try:
            destination = resolve_path(config_path, config.get("destination"))
            destination.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.fromisoformat(report["started_at"]).strftime(
                "%Y-%m-%d_%H-%M"
            )
            with TemporaryDirectory(
                prefix=f"folyamatban-{timestamp}-", dir=destination
            ) as temporary:
                staging = Path(temporary)
                failure_directory = destination / staging.name.replace("folyamatban-", "hiba-", 1)
                report["archive_name"] = None
                report["archive_size_bytes"] = None
                report["backup_directory"] = str(failure_directory)
                write_report(staging / f"backup_{timestamp}.json", report)
                staging.rename(failure_directory)
        except OSError as report_error:
            report["report_error"] = str(report_error)
            try:
                write_report(
                    log_path.parent / f"backup_failed_{uuid4().hex}.json", report
                )
            except OSError as fallback_error:
                report["report_error"] += f"; Tartalék jelentés: {fallback_error}"
        raise
    finally:
        log_report(logger, report)


def build_backup(config_path, config, report, started, log_path):
    if not config["sources"]:
        raise ValueError("A sources mezőben adj meg legalább egy mappát.")

    sources = [resolve_path(config_path, source) for source in config["sources"]]
    destination = resolve_path(config_path, config.get("destination"))
    report["sources"] = [str(source) for source in sources]
    for source in sources:
        if log_path.is_relative_to(source):
            raise ValueError("A naplófájl nem lehet a mentendő mappán belül.")
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
        report["archive_name"] = archive.name
        report["archive_size_bytes"] = archive.stat().st_size
        report["backup_directory"] = str(backup_path)
        finish_report(report, started)
        write_report(staging / f"backup_{timestamp}.json", report)
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
