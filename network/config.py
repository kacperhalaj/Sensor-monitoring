import yaml
from typing import Dict, Any


def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """
    Wczytuje konfigurację sieciową z pliku YAML.

    :param config_path: Ścieżka do pliku konfiguracyjnego
    :return: Słownik zawierający konfigurację
    """
    try:
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
            return config.get("network", {})
    except (FileNotFoundError, yaml.YAMLError) as e:
        print(f"Uwaga: Nie można wczytać pliku konfiguracyjnego '{config_path}'. Używam wartości domyślnych.")
        return {"client": {}, "server": {}}