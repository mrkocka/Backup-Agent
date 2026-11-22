import argparse
import json
import math
import os
import smtplib
import ssl
import sys
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path


def create_message(report, sender, recipient):
    if not isinstance(report, dict) or report.get("status") not in ("success", "failed"):
        raise ValueError("Érvénytelen mentési eredmény.")
    duration = report.get("duration_seconds")
    if isinstance(duration, bool) or not isinstance(duration, (int, float)):
        raise ValueError("Hiányzó vagy hibás időtartam.")
    if not math.isfinite(duration) or duration < 0:
        raise ValueError("Érvénytelen időtartam.")
    started = datetime.fromisoformat(report["started_at"])
    finished = datetime.fromisoformat(report["finished_at"])
    size = report.get("archive_size_bytes")
    if size is not None and (type(size) is not int or size < 0):
        raise ValueError("Érvénytelen archívumméret.")

    size_text = f"{size} bájt" if size is not None else "Nem ismert"
    status = "SIKERES" if report["status"] == "success" else "SIKERTELEN"
    message = EmailMessage()
    message["Subject"] = f"Backup-Agent - Helyi mentés {status}"
    message["From"] = sender
    message["To"] = recipient
    message.set_content(
        f"Helyi mentés eredménye: {status}\n"
        f"Kezdés: {started.isoformat(sep=' ', timespec='seconds')}\n"
        f"Befejezés: {finished.isoformat(sep=' ', timespec='seconds')}\n"
        f"Időtartam: {duration:.3f} másodperc\n"
        f"Archívum: {report.get('archive_name') or 'Nem készült el'}\n"
        f"Méret: {size_text}\n"
        f"Hiba: {report.get('error') or 'Nincs'}\n\n"
        "Az értesítés a helyi mentés JSON-jelentése alapján készült.\n"
        "A fogadóoldali archívumellenőrzés még nincs bekötve.\n"
    )
    return message


def load_env(path):
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        key, separator, value = line.partition("=")
        if not separator or not key.strip():
            raise ValueError("Hibás .env sor. A várt alak KULCS=érték.")
        os.environ.setdefault(key.strip(), value.strip())


def send_message(message):
    if not os.environ["SMTP_PASSWORD"].isascii():
        raise ValueError(
            "Az SMTP-jelszó ékezetes vagy más nem ASCII karaktert tartalmaz. "
            "A jelenlegi SMTP-hitelesítés ASCII jelszót igényel. "
            "Ellenőrizd a server/.env SMTP_PASSWORD beállítását."
        )
    host = os.environ["SMTP_HOST"]
    port = int(os.environ.get("SMTP_PORT", "465"))
    with smtplib.SMTP_SSL(host, port, timeout=30, context=ssl.create_default_context()) as smtp:
        smtp.login(os.environ["SMTP_USER"], os.environ["SMTP_PASSWORD"])
        smtp.send_message(message)


def main():
    parser = argparse.ArgumentParser(description="Értesítés egy mentési JSON-jelentésből.")
    parser.add_argument("report", type=Path, help="A mentési JSON-fájl.")
    parser.add_argument("--send", action="store_true", help="E-mail tényleges elküldése.")
    args = parser.parse_args()
    try:
        load_env(Path(__file__).resolve().with_name(".env"))
        report = json.loads(args.report.read_text(encoding="utf-8"))
        message = create_message(
            report,
            os.environ.get("MAIL_FROM", "backup@example.invalid"),
            os.environ.get("MAIL_TO", "operator@example.invalid"),
        )
        if args.send:
            for key in ("SMTP_HOST", "SMTP_USER", "SMTP_PASSWORD", "MAIL_FROM", "MAIL_TO"):
                if not os.environ.get(key):
                    raise ValueError(f"Hiányzó beállítás: {key}")
            send_message(message)
            print("Az SMTP-szerver átvette az értesítést.")
        else:
            print(f"Tárgy: {message['Subject']}\n")
            print(message.get_content())
    except (OSError, ValueError, KeyError, TypeError, smtplib.SMTPException) as error:
        sys.exit(f"Értesítési hiba: {error}")


if __name__ == "__main__":
    main()
