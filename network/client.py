import socket
import json
import time
import yaml
from datetime import datetime
from typing import Dict, Any, Optional


class NetworkClient:
    """
    Klient sieciowy do komunikacji z serwerem poprzez protokół TCP.
    Umożliwia wysyłanie danych w formacie JSON oraz odbieranie potwierdzeń.
    """

    def __init__(
            self,
            host: str = None,
            port: int = None,
            timeout: float = None,
            retries: int = None,
            config_path: str = "config.yaml",
            logger=None
    ):
        """
        Inicjalizuje klienta sieciowego.

        :param host: Adres hosta serwera
        :param port: Port serwera
        :param timeout: Timeout połączenia w sekundach
        :param retries: Liczba prób ponowienia w przypadku błędu
        :param config_path: Ścieżka do pliku konfiguracyjnego
        :param logger: Opcjonalny obiekt loggera do rejestrowania zdarzeń
        """

        self.logger = logger

        # Ładowanie konfiguracji z pliku
        config = self._load_config(config_path)

        # Parametry konstruktora nadpisują konfigurację z pliku
        self.host = host if host is not None else config.get("host", "127.0.0.1")
        self.port = port if port is not None else config.get("port", 5000)
        self.timeout = timeout if timeout is not None else config.get("timeout", 5.0)
        self.retries = retries if retries is not None else config.get("retries", 3)

        self.sock = None
        self.connected = False

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """
        Wczytuje konfigurację z pliku YAML.

        :param config_path: Ścieżka do pliku konfiguracyjnego
        :return: Słownik z konfiguracją dla klienta
        """
        try:
            with open(config_path, 'r') as file:
                config = yaml.safe_load(file)
                return config.get("network", {}).get("client", {})
        except (FileNotFoundError, yaml.YAMLError) as e:
            if self.logger:
                self.logger.log_reading("NETWORK", datetime.now(), f"Błąd wczytywania konfiguracji: {str(e)}", "ERROR")
            print(f"Uwaga: Nie można wczytać pliku konfiguracyjnego '{config_path}'. Używam wartości domyślnych.")
            return {}

    def connect(self) -> bool:
        """
        Nawiązuje połączenie z serwerem.

        :return: True jeśli połączenie nawiązane, False w przypadku błędu
        """
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(self.timeout)
            self.sock.connect((self.host, self.port))
            self.connected = True

            if self.logger:
                self.logger.log_reading("NETWORK", datetime.now(),
                                        f"Nawiązano połączenie z {self.host}:{self.port}", "INFO")
            return True
        except Exception as e:
            if self.logger:
                self.logger.log_reading("NETWORK", datetime.now(),
                                        f"Błąd połączenia: {str(e)}", "ERROR")
            print(f"Błąd połączenia: {str(e)}")
            self.connected = False
            return False

    def send(self, data: dict) -> bool:
        """
        Wysyła dane i czeka na potwierdzenie zwrotne.

        :param data: Słownik z danymi do wysłania
        :return: True w przypadku sukcesu, False w przypadku błędu
        """
        if not self.connected:
            if not self.connect():
                return False

        serialized_data = self._serialize(data)

        for attempt in range(self.retries):
            try:
                # Wysyłanie danych
                self.sock.sendall(serialized_data)

                if self.logger:
                    self.logger.log_reading("NETWORK", datetime.now(),
                                            f"Wysłano dane: {data}", "INFO")

                # Oczekiwanie na potwierdzenie
                response = self.sock.recv(1024)

                if response.strip() == b"ACK":
                    if self.logger:
                        self.logger.log_reading("NETWORK", datetime.now(),
                                                "Otrzymano potwierdzenie ACK", "INFO")
                    return True
                else:
                    if self.logger:
                        self.logger.log_reading("NETWORK", datetime.now(),
                                                f"Nieoczekiwana odpowiedź: {response.decode('utf-8')}", "WARNING")

            except Exception as e:
                if self.logger:
                    self.logger.log_reading("NETWORK", datetime.now(),
                                            f"Próba {attempt + 1}/{self.retries}: Błąd komunikacji: {str(e)}", "ERROR")
                print(f"Próba {attempt + 1}/{self.retries}: Błąd komunikacji: {str(e)}")

                # Próba ponownego połączenia
                self.close()
                time.sleep(1)  # Krótkie opóźnienie przed ponowną próbą
                if not self.connect():
                    continue

        return False

    def close(self) -> None:
        """
        Zamyka połączenie.
        """
        if self.sock:
            try:
                self.sock.close()
                if self.logger:
                    self.logger.log_reading("NETWORK", datetime.now(),
                                            "Zamknięto połączenie", "INFO")
            except Exception as e:  # Używamy Exception zamiast socket.error
                if self.logger:
                    self.logger.log_reading("NETWORK", datetime.now(),
                                            f"Błąd przy zamykaniu połączenia: {str(e)}", "ERROR")
                print(f"Błąd przy zamykaniu połączenia: {str(e)}")
            finally:
                self.sock = None
                self.connected = False

    def _serialize(self, data: dict) -> bytes:
        """
        Serializuje słownik do formatu JSON z dodaniem znaku nowej linii.

        :param data: Słownik do serializacji
        :return: Zserializowane dane w formacie bajtowym
        """
        json_str = json.dumps(data)
        return (json_str + "\n").encode('utf-8')

    def _deserialize(self, raw: bytes) -> dict:
        """
        Deserializuje dane JSON z formatu bajtowego.

        :param raw: Dane w formacie bajtowym
        :return: Zdserializowany słownik
        """
        return json.loads(raw.decode('utf-8'))