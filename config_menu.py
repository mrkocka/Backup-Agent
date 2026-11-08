from backup_config import load_config, resolve_path, save_config


def add_source(config_path, config):
    value = input("Új forrásmappa (üres = vissza): ").strip()
    if not value:
        return

    source = resolve_path(config_path, value)
    destination = resolve_path(config_path, config.get("destination"))
    if not source.is_dir():
        raise ValueError(f"A forrásmappa nem található: {source}")
    if destination.is_relative_to(source):
        raise ValueError("A mentés célja nem lehet a forrásmappán belül.")
    if any(source == resolve_path(config_path, item) for item in config["sources"]):
        raise ValueError("Ez a forrásmappa már szerepel a listában.")

    save_config(config_path, {**config, "sources": [*config["sources"], value]})
    print("Forrásmappa hozzáadva.")


def remove_source(config_path, config):
    sources = config["sources"].copy()
    if not sources:
        print("Nincs eltávolítható forrásmappa.")
        return

    value = input("Az eltávolítandó mappa sorszáma (üres = vissza): ").strip()
    if not value:
        return
    try:
        number = int(value)
    except ValueError:
        raise ValueError("Adj meg egy sorszámot a listából.") from None
    if not 1 <= number <= len(sources):
        raise ValueError("Adj meg egy sorszámot a listából.")

    sources.pop(number - 1)
    save_config(config_path, {**config, "sources": sources})
    print("Forrásmappa eltávolítva a konfigurációból.")


def run_config_menu(config_path):
    actions = {"1": add_source, "2": remove_source}
    try:
        while True:
            config = load_config(config_path)
            print("\nMentendő mappák:")
            for number, source in enumerate(config["sources"], start=1):
                print(f"  {number}. {source}")
            if not config["sources"]:
                print("  A lista üres.")

            print("\n1. Hozzáadás   2. Eltávolítás   0. Kilépés")
            choice = input("Választás: ").strip()
            if choice == "0":
                return
            if choice not in actions:
                print("Válassz a menüpontok közül.")
                continue

            try:
                actions[choice](config_path, config)
            except (OSError, ValueError, RuntimeError) as error:
                print(f"Konfigurációs hiba: {error}")
    except (EOFError, KeyboardInterrupt):
        print()
