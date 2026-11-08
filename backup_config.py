import json
from pathlib import Path
from tempfile import TemporaryDirectory


CONFIG_PATH = Path(__file__).resolve().with_name("config.json")


def load_config(path):
    config = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(config, dict):
        raise ValueError("A konfigurációnak JSON-objektumnak kell lennie.")
    sources = config.get("sources")
    if not isinstance(sources, list) or any(
        not isinstance(source, str) or not source.strip() for source in sources
    ):
        raise ValueError("A sources mezőben mappaútvonalak listája szükséges.")
    return config


def resolve_path(config_path, value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Minden elérési út legyen nem üres szöveg.")
    return (config_path.parent / Path(value).expanduser()).resolve()


def save_config(path, config):
    path = path.resolve()
    with TemporaryDirectory(dir=path.parent) as directory:
        temporary = Path(directory) / path.name
        temporary.write_text(
            json.dumps(config, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        temporary.chmod(path.stat().st_mode & 0o777)
        temporary.replace(path)
