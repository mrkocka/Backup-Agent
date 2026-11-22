import json
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from time import perf_counter


def open_log(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.Logger("backup-agent")
    handler = RotatingFileHandler(
        path, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)
    return logger


def finish_report(report, started, error=None):
    report.update(
        finished_at=datetime.now().astimezone().isoformat(),
        duration_seconds=round(perf_counter() - started, 6),
        status="failed" if error else "success",
        error=str(error) if error else None,
    )


def write_report(path, report):
    path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def log_report(logger, report):
    started = datetime.fromisoformat(report["started_at"]).isoformat(
        sep=" ", timespec="seconds"
    )
    finished = datetime.fromisoformat(report["finished_at"]).isoformat(
        sep=" ", timespec="seconds"
    )
    size = report.get("archive_size_bytes")
    size_text = "Nem készült el"
    if size is not None:
        size_text = f"{size / (1024 * 1024):.2f} MiB ({size:,} bájt)"

    lines = [
        "=" * 60,
        f"Mentés eredménye: {'SIKERES' if report['status'] == 'success' else 'SIKERTELEN'}",
        f"Kezdés: {started}",
        f"Befejezés: {finished}",
        f"Időtartam: {report['duration_seconds']:.3f} másodperc",
        f"Archívum: {report.get('archive_name') or 'Nem készült el'}",
        f"Méret: {size_text}",
        f"Mentési mappa: {report.get('backup_directory', 'Nem jött létre')}",
        "Forrásmappák:",
    ]
    lines.extend(f"  - {source}" for source in report.get("sources", []))
    lines.append(f"Hiba: {report.get('error') or 'Nincs'}")
    if report.get("report_error"):
        lines.append(f"Eredményfájl írási hibája: {report['report_error']}")
    lines.append("")
    logger.info("\n".join(lines))
    for handler in logger.handlers[:]:
        handler.close()
        logger.removeHandler(handler)
