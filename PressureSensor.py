import requests
from datetime import datetime
from sensor import Sensor

class PressureSensor(Sensor):
    def __init__(self, sensor_id, name, unit, min_value, max_value, api_key, city):
        super().__init__(sensor_id, name, unit, min_value, max_value)
        self.api_key = api_key
        self.city = city

    def read_value(self):
        if not self.active:
            raise Exception(f"Czujnik {self.name} jest wyłączony.")

        # API OpenWeatherMap
        url = f"http://api.openweathermap.org/data/2.5/weather?q={self.city}&appid={self.api_key}&units=metric"
        response = requests.get(url)
        data = response.json()

        # odpowiedz
        if 'main' not in data or 'pressure' not in data['main']:
            print(f"Problem z odpowiedzią API: {data}")
            raise Exception("Brak danych o ciśnieniu.")

        pressure = data['main']['pressure']
        self.last_value = round(min(max(pressure, self.min_value), self.max_value), 2)

        # data
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] Odczyt ciśnienia ({self.name}): {self.last_value} {self.unit}")
        return self.last_value
