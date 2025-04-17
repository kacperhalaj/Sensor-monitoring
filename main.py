import time
from TemperatureSensor import TemperatureSensor
from HumiditySensor import HumiditySensor
from PressureSensor import PressureSensor
from LightSensor import LightSensor
from AirQualitySensor import AirQualitySensor
from AccelerometerSensor import AccelerometerSensor
from ProximitySensor import ProximitySensor

API_KEY = "77fd14fe50e6ccd5d66cfd6c83d9d255"
CITY = "Warsaw"
# LAT = 52.2297
# LON = 21.0122
AQICN_TOKEN = "f033dbd191aa8762aac0ac0d1d19d7770066d737"


# czujniki
temp_sensor = TemperatureSensor("T1", "Czujnik temperatury", "°C", -20, 50, API_KEY, CITY)
humidity_sensor = HumiditySensor("H1", "Czujnik wilgotności", "%", 0, 100, API_KEY, CITY)
pressure_sensor = PressureSensor("P1", "Czujnik ciśnienia", "hPa", 950, 1050, API_KEY, CITY)
light_sensor = LightSensor("L1", "Czujnik światła", "lux", 0, 10000, API_KEY, CITY)
# air_quality_sensor = AirQualitySensor("A1", "Czujnik jakości powietrza", "AQI", 0, 500, API_KEY, LAT, LON)
air_quality_sensor = AirQualitySensor("A1", "Czujnik jakości powietrza", "AQI", 0, 500, AQICN_TOKEN, CITY)
accelerometer_sensor = AccelerometerSensor("ACC1", "Czujnik akcelerometru", "g", -16, 16)
proximity_sensor = ProximitySensor("PRX1", "Czujnik zbliżeniowy", "cm", 0, 200)

# odczyty
num_readings = 3
duration = 1
interval = duration / num_readings

for i in range(num_readings):
    print(f"\n--- Odczyt {i + 1} ---")
    temp_sensor.read_value()
    humidity_sensor.read_value()
    pressure_sensor.read_value()
    light_sensor.read_value()
    air_quality_sensor.read_value()
    accelerometer_sensor.read_value()
    proximity_sensor.read_value()
    time.sleep(interval)
