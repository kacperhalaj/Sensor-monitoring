import socket
import json
import yaml
import sys
from threading import Thread
from typing import Dict, Any, Callable, List


class NetworkServer:
    """
    Prosty serwer TCP do odbierania danych w formacie JSON i wysyłania potwierdzeń.
    Obsługuje rejestrację callbacków na nowe odczyty.
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

        self._callbacks: List[Callable[[dict], None]] = []
        self._server_socket = None

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

    def register_callback(self, func: Callable[[dict], None]):
        """Dodaje funkcję do listy callbacków wywoływanych przy nowym odczycie."""
        self._callbacks.append(func)

    def _notify_callbacks(self, data: dict):
        for cb in self._callbacks:
            try:
                cb(data)
            except Exception as e:
                print(f"Błąd w callbacku: {str(e)}", file=sys.stderr)

    def start(self) -> None:
        """
        Uruchamia nasłuchiwanie połączeń i obsługę klientów.
        """
        try:
            self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # Pozwala na natychmiastowe ponowne użycie portu
            self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._server_socket.bind(('0.0.0.0', self.port))
            self._server_socket.listen(5)

            print(f"Serwer uruchomiony na porcie {self.port}")
            self.running = True

            while self.running:
                try:
                    self._server_socket.settimeout(1.0)
                    try:
                        client_socket, addr = self._server_socket.accept()
                    except socket.timeout:
                        continue
                    print(f"Nowe połączenie od {addr[0]}:{addr[1]}")

                    # Obsługa klienta w osobnym wątku
                    client_thread = Thread(target=self._handle_client, args=(client_socket, addr))
                    client_thread.daemon = True
                    client_thread.start()

                except socket.error as e:
                    if self.running:
                        print(f"Błąd podczas akceptowania połączenia: {str(e)}", file=sys.stderr)

        except socket.error as e:
            print(f"Błąd podczas uruchamiania serwera: {str(e)}", file=sys.stderr)
        finally:
            if self._server_socket:
                self._server_socket.close()
                self._server_socket = None

    def stop(self):
        """Zatrzymuje serwer i zamyka gniazdo."""
        self.running = False
        if self._server_socket:
            try:
                self._server_socket.close()
            except Exception:
                pass
            self._server_socket = None
        print("Serwer zatrzymany.")

    def _handle_client(self, client_socket, addr) -> None:
        """
        Odbiera dane, wysyła ACK i wypisuje je na konsolę.

        :param client_socket: Gniazdo klienta
        :param addr: Adres klienta
        """
        try:
            buffer = ""

            while True:
                data = client_socket.recv(1024)
                if not data:
                    break

                buffer += data.decode('utf-8')

                # Przetwarzaj wszystkie kompletne linie JSON (każda kończy się '\n')
                while '\n' in buffer:
                    message, buffer = buffer.split('\n', 1)

                    try:
                        # Deserializacja JSON
                        json_data = json.loads(message)

                        # Wypisanie na konsolę
                        print(f"\nOdebrano dane od {addr[0]}:{addr[1]}:")
                        for key, value in json_data.items():
                            print(f"  {key}: {value}")

                        # Powiadom callbacki
                        self._notify_callbacks(json_data)

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
    try:
        server.start()
    except KeyboardInterrupt:
        print("\nZatrzymywanie serwera...")
        server.stop()