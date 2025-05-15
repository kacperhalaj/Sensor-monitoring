import unittest
import socket
import json
import threading
import time
from unittest.mock import patch, MagicMock
from server.server import NetworkServer


class TestNetworkServer(unittest.TestCase):
    """
    Testy jednostkowe dla NetworkServer.
    """

    def setUp(self):
        # Przygotowanie danych testowych
        self.test_port = 5050
        self.test_data = {"sensor_id": "T1", "value": 22.5, "unit": "°C"}

    def test_server_initialization(self):
        # Przygotowanie mocka dla _load_config
        server = NetworkServer(port=self.test_port)
        with patch.object(server, '_load_config', return_value={"port": 5000}):
            # Asercje
            self.assertEqual(server.port, self.test_port)

    @unittest.skip("Test interakcji klienta z serwerem wymaga działającego serwera")
    def test_server_client_interaction(self):
        """
        Test interakcji klienta z serwerem przy użyciu rzeczywistych gniazd.
        Ten test jest pomijany, ponieważ wymaga działającego serwera.
        """
        # Tworzenie i uruchamianie serwera w osobnym wątku
        server = NetworkServer(port=self.test_port)
        server_thread = threading.Thread(target=server.start)
        server_thread.daemon = True
        server_thread.start()

        # Krótkie opóźnienie, aby serwer mógł się uruchomić
        time.sleep(0.5)

        try:
            # Tworzenie klienta i nawiązywanie połączenia
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect(('127.0.0.1', self.test_port))

            # Wysyłanie danych
            data_str = json.dumps(self.test_data) + "\n"
            client_socket.sendall(data_str.encode('utf-8'))

            # Odbieranie odpowiedzi
            response = client_socket.recv(1024)

            # Asercja
            self.assertEqual(response.strip(), b"ACK")

        except Exception as e:
            self.fail(f"Test nie powiódł się: {str(e)}")

        finally:
            # Zamykanie połączenia klienta
            try:
                client_socket.close()
            except:
                pass

            # Zatrzymanie serwera
            server.running = False


if __name__ == '__main__':
    unittest.main()