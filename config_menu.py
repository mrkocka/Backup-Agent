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


def change_log_file(config_path, config):
    value = input("Új naplófájl útvonala (üres = vissza): ").strip()
    if not value:
        return

    log_path = resolve_path(config_path, value)
    if log_path.is_dir():
        raise ValueError("Fájlelérési utat adj meg, például logs/backup.log.")
    for source in config["sources"]:
        if log_path.is_relative_to(resolve_path(config_path, source)):
            raise ValueError("A naplófájl nem lehet a mentendő mappán belül.")

    save_config(config_path, {**config, "log_file": value})
    print("Naplófájl útvonala módosítva.")


def run_config_menu(config_path):
    actions = {"1": add_source, "2": remove_source, "3": change_log_file}
    try:
        while True:
            config = load_config(config_path)
            print("\nMentendő mappák:")
            for number, source in enumerate(config["sources"], start=1):
                print(f"  {number}. {source}")
            if not config["sources"]:
                print("  A lista üres.")

            print(f"\nNaplófájl: {config.get('log_file', 'logs/backup.log')}")
            print("\n1. Hozzáadás   2. Eltávolítás   3. Napló helye   0. Kilépés")
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
