import unittest
import json
import socket
from unittest.mock import MagicMock, patch
from network.client import NetworkClient


class TestNetworkClient(unittest.TestCase):
    """
    Testy jednostkowe dla NetworkClient.
    """

    def setUp(self):
        # Przygotowanie mocków i danych testowych
        self.mock_logger = MagicMock()
        self.test_data = {"sensor_id": "T1", "value": 22.5, "unit": "°C"}
        self.mock_config = {"host": "test.example.com", "port": 5000, "timeout": 2.0, "retries": 2}

    @patch('network.client.socket.socket')
    def test_connect_success(self, mock_socket):
        # Przygotowanie
        mock_sock = MagicMock()
        mock_socket.return_value = mock_sock

        # Tworzenie klienta z bezpośrednim przekazaniem parametrów
        client = NetworkClient(
            host=self.mock_config["host"],
            port=self.mock_config["port"],
            timeout=self.mock_config["timeout"],
            retries=self.mock_config["retries"],
            logger=self.mock_logger
        )

        # Wywołanie metody connect
        result = client.connect()

        # Asercje
        self.assertTrue(result)
        mock_sock.connect.assert_called_once_with((self.mock_config["host"], self.mock_config["port"]))
        self.assertTrue(client.connected)

    def test_connect_failure(self):
        # Przygotowanie
        with patch('network.client.socket.socket') as mock_socket:
            mock_sock = MagicMock()
            mock_sock.connect.side_effect = Exception("Connection refused")
            mock_socket.return_value = mock_sock

            # Tworzenie klienta z bezpośrednim przekazaniem parametrów
            client = NetworkClient(
                host=self.mock_config["host"],
                port=self.mock_config["port"],
                timeout=self.mock_config["timeout"],
                retries=self.mock_config["retries"],
                logger=self.mock_logger
            )

            # Wywołanie metody connect
            result = client.connect()

            # Asercje
            self.assertFalse(result)
            self.assertFalse(client.connected)

    @patch('network.client.socket.socket')
    def test_send_success(self, mock_socket):
        # Przygotowanie
        mock_sock = MagicMock()
        mock_sock.recv.return_value = b"ACK"
        mock_socket.return_value = mock_sock

        # Tworzenie klienta z bezpośrednim przekazaniem parametrów
        client = NetworkClient(
            host=self.mock_config["host"],
            port=self.mock_config["port"],
            timeout=self.mock_config["timeout"],
            retries=self.mock_config["retries"],
            logger=self.mock_logger
        )

        # Ustawienie stanu klienta jako połączonego
        client.connected = True
        client.sock = mock_sock

        # Wywołanie metody send
        result = client.send(self.test_data)

        # Asercje
        self.assertTrue(result)
        expected_data = (json.dumps(self.test_data) + "\n").encode('utf-8')
        mock_sock.sendall.assert_called_once_with(expected_data)

    def test_send_failure(self):
        # Przygotowanie
        with patch('network.client.socket.socket') as mock_socket:
            mock_sock = MagicMock()
            mock_sock.sendall.side_effect = Exception("Connection reset")
            mock_socket.return_value = mock_sock

            # Tworzenie klienta z bezpośrednim przekazaniem parametrów
            client = NetworkClient(
                host=self.mock_config["host"],
                port=self.mock_config["port"],
                timeout=self.mock_config["timeout"],
                retries=self.mock_config["retries"],
                logger=self.mock_logger
            )

            # Ustawienie stanu klienta jako połączonego
            client.connected = True
            client.sock = mock_sock

            # Zastąpienie metody connect, aby nie próbowała się ponownie łączyć
            with patch.object(client, 'connect', return_value=False):
                # Wywołanie metody send
                result = client.send(self.test_data)

            # Asercje
            self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()