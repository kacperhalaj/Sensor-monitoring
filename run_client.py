import time
from datetime import datetime
import signal
import sys

from TemperatureSensor import TemperatureSensor
from HumiditySensor import HumiditySensor
from PressureSensor import PressureSensor
from LightSensor import LightSensor
from AirQualitySensor import AirQualitySensor
from AccelerometerSensor import AccelerometerSensor
from ProximitySensor import ProximitySensor
from Logger import Logger
from network.client import NetworkClient

API_KEY = "77fd14fe50e6ccd5d66cfd6c83d9d255"
CITY = "Rzeszow"
AQICN_TOKEN = "f033dbd191aa8762aac0ac0d1d19d7770066d737"

def main():
    # Konfiguracja loggera
    logger = Logger(config_path="config.json")

    # Inicjalizacja klienta sieciowego
    network_client = NetworkClient(logger=logger)

    # Obsługa zamknięcia aplikacji
    def signal_handler(sig, frame):
        print("\nZatrzymywanie aplikacji...")
        logger.stop()
        network_client.close()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    # Czujniki
    temp_sensor = TemperatureSensor("T1", "Czujnik temperatury", "°C", -20, 50, API_KEY, CITY, logger)
    humidity_sensor = HumiditySensor("H1", "Czujnik wilgotności", "%", 0, 100, API_KEY, CITY, logger)
    pressure_sensor = PressureSensor("P1", "Czujnik ciśnienia", "hPa", 950, 1050, API_KEY, CITY, logger)
    light_sensor = LightSensor("L1", "Czujnik światła", "lux", 0, 10000, API_KEY, CITY, logger)
    air_quality_sensor = AirQualitySensor("A1", "Czujnik jakości powietrza", "AQI", 0, 500, AQICN_TOKEN, CITY, logger)
    accelerometer_sensor = AccelerometerSensor("ACC1", "Czujnik akcelerometru", "g", -16, 16, logger)
    proximity_sensor = ProximitySensor("PRX1", "Czujnik zbliżeniowy", "cm", 0, 200, logger)

    # logowanie start
    logger.start()

    # Odczyty
    num_readings = 10
    duration = 0.1
    interval = duration / num_readings

    for i in range(num_readings):
        print(f"\n--- Odczyt {i + 1} ---")

        # Odczyt wartości z czujników
        temp_value = temp_sensor.read_value()
        humidity_value = humidity_sensor.read_value()
        pressure_value = pressure_sensor.read_value()
        light_value = light_sensor.read_value()
        air_quality_value = air_quality_sensor.read_value()
        accelerometer_value = accelerometer_sensor.read_value()
        proximity_value = proximity_sensor.read_value()

        # Przygotowanie danych do wysłania
        sensor_data = {
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "readings": {
                "temperature": {"value": temp_value, "unit": "°C", "sensor_id": "T1"},
                "humidity": {"value": humidity_value, "unit": "%", "sensor_id": "H1"},
                "pressure": {"value": pressure_value, "unit": "hPa", "sensor_id": "P1"},
                "light": {"value": light_value, "unit": "lux", "sensor_id": "L1"},
                "air_quality": {"value": air_quality_value, "unit": "AQI", "sensor_id": "A1"},
                "proximity": {"value": proximity_value, "unit": "cm", "sensor_id": "PRX1"}
            }
        }

        # Wysłanie danych do serwera
        try:
            if network_client.send(sensor_data):
                print("Dane pomyślnie wysłane do serwera")
            else:
                print("Nie udało się wysłać danych do serwera")
        except Exception as e:
            print(f"Błąd podczas wysyłania danych: {str(e)}")

        time.sleep(interval)

    # logowanie stop
    logger.stop()
    # Zamknięcie połączenia sieciowego
    network_client.close()


if __name__ == "__main__":
    main()