import socket
import json
import yaml
import sys
from threading import Thread
from typing import Dict, Any


class NetworkServer:
    """
    Prosty serwer TCP do odbierania danych w formacie JSON i wysyłania potwierdzeń.
    """

    def __init__(self, port: int = None, config_path: str = "config.yaml"):
        """
        Inicjalizuje serwer na wskazanym porcie.

        :param port: Port nasłuchiwania
        :param config_path: Ścieżka do pliku konfiguracyjnego
        """
        config = self._load_config(config_path)
        self.port = port if port is not None else config.get("port", 5000)
        self.running = False

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """
        Wczytuje konfigurację z pliku YAML.

        :param config_path: Ścieżka do pliku konfiguracyjnego
        :return: Słownik z konfiguracją dla serwera
        """
        try:
            with open(config_path, 'r') as file:
                config = yaml.safe_load(file)
                return config.get("network", {}).get("server", {})
        except (FileNotFoundError, yaml.YAMLError) as e:
            print(f"Uwaga: Nie można wczytać pliku konfiguracyjnego '{config_path}'. Używam wartości domyślnych.")
            return {}

    def start(self) -> None:
        """
        Uruchamia nasłuchiwanie połączeń i obsługę klientów.
        """
        try:
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # Pozwala na natychmiastowe ponowne użycie portu
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind(('0.0.0.0', self.port))
            server_socket.listen(5)

            print(f"Serwer uruchomiony na porcie {self.port}")
            self.running = True

            while self.running:
                try:
                    client_socket, addr = server_socket.accept()
                    print(f"Nowe połączenie od {addr[0]}:{addr[1]}")

                    # Obsługa klienta w osobnym wątku
                    client_thread = Thread(target=self._handle_client, args=(client_socket, addr))
                    client_thread.daemon = True
                    client_thread.start()

                except socket.error as e:
                    print(f"Błąd podczas akceptowania połączenia: {str(e)}", file=sys.stderr)

        except socket.error as e:
            print(f"Błąd podczas uruchamiania serwera: {str(e)}", file=sys.stderr)
        finally:
            server_socket.close()

    def _handle_client(self, client_socket, addr) -> None:
        """
        Odbiera dane, wysyła ACK i wypisuje je na konsolę.

        :param client_socket: Gniazdo klienta
        :param addr: Adres klienta
        """
        try:
            # Bufor do przechowywania danych
            buffer = ""

            while True:
                data = client_socket.recv(1024)
                if not data:
                    break

                buffer += data.decode('utf-8')

                # Sprawdzanie, czy otrzymaliśmy pełny JSON (zakończony nową linią)
                if '\n' in buffer:
                    message, buffer = buffer.split('\n', 1)

                    try:
                        # Deserializacja JSON
                        json_data = json.loads(message)

                        # Wypisanie na konsolę
                        print(f"\nOdebrano dane od {addr[0]}:{addr[1]}:")
                        for key, value in json_data.items():
                            print(f"  {key}: {value}")

                        # Wysłanie potwierdzenia
                        client_socket.sendall(b"ACK\n")

                    except json.JSONDecodeError as e:
                        print(f"Błąd parsowania JSON: {str(e)}", file=sys.stderr)
                        client_socket.sendall(b"ERROR: Invalid JSON\n")

        except socket.error as e:
            print(f"Błąd podczas obsługi klienta {addr[0]}:{addr[1]}: {str(e)}", file=sys.stderr)

        finally:
            client_socket.close()
            print(f"Zamknięto połączenie z {addr[0]}:{addr[1]}")


# Uruchomienie serwera
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Prosty serwer TCP do odbierania danych JSON")
    parser.add_argument("--port", type=int, help="Port nasłuchiwania")
    parser.add_argument("--config", help="Ścieżka do pliku konfiguracyjnego", default="config.yaml")

    args = parser.parse_args()

    server = NetworkServer(port=args.port, config_path=args.config)
    server.start()