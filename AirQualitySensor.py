import requests
from datetime import datetime
from sensor import Sensor

class AirQualitySensor(Sensor):
    def __init__(self, sensor_id, name, unit, min_value, max_value, api_token, city, logger=None):
        super().__init__(sensor_id, name, unit, min_value, max_value)
        self.api_token = api_token
        self.city = city
        self.logger = logger

    def read_value(self):
        if not self.active:
            raise Exception(f"Czujnik {self.name} jest wyłączony.")

        # API AQICN
        url = f"https://api.waqi.info/feed/{self.city}/?token={self.api_token}"
        response = requests.get(url)
        data = response.json()

        # odpowiedz
        if "data" not in data or "aqi" not in data["data"]:
            print(f"Problem z odpowiedzią API AQICN: {data}")
            raise Exception("Brak danych o jakości powietrza w odpowiedzi API AQICN.")

        aqi = data["data"]["aqi"]
        self.last_value = round(min(max(aqi, self.min_value), self.max_value), 2)

        # zapis do logu
        if self.logger:
            timestamp = datetime.now()
            self.logger.log_reading(self.sensor_id, timestamp, self.last_value, self.unit)

        # data
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] Odczyt jakości powietrza ({self.name}): {self.last_value} {self.unit}")
        return self.last_value
