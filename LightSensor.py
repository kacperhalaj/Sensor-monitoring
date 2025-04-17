import requests
from datetime import datetime
from sensor import Sensor

class LightSensor(Sensor):
    def __init__(self, sensor_id, name, unit, min_value, max_value, api_key, city):
        super().__init__(sensor_id, name, unit, min_value, max_value)
        self.api_key = api_key
        self.city = city

    def read_value(self):
        if not self.active:
            raise Exception(f"Czujnik {self.name} jest wyłączony.")

        # API OpenWeatherMap
        url = f"http://api.openweathermap.org/data/2.5/weather?q={self.city}&appid={self.api_key}"
        response = requests.get(url)
        data = response.json()

        weather = data.get("weather", [{}])[0].get("main", "").lower()

        # przykladowe lx
        base_light = {
            "clear": 10000,
            "clouds": 5000,
            "rain": 200,
            "drizzle": 300,
            "thunderstorm": 100,
            "snow": 800,
            "mist": 100,
            "fog": 50
        }.get(weather, 200)

        self.last_value = round(min(max(base_light, self.min_value), self.max_value), 2)

        # data
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] Odczyt natężenia światła ({self.name}): {self.last_value} {self.unit}")
        return self.last_value
