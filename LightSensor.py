import requests
from datetime import datetime
from sensor import Sensor

class LightSensor(Sensor):
    def __init__(self, sensor_id, name, unit, min_value, max_value, api_key, city, logger=None):
        super().__init__(sensor_id, name, unit, min_value, max_value)
        self.api_key = api_key
        self.city = city
        self.logger = logger

    def read_value(self):
        if not self.active:
            raise Exception(f"Czujnik {self.name} jest wyłączony.")

        # API OpenWeatherMap
        url = f"http://api.openweathermap.org/data/2.5/weather?q={self.city}&appid={self.api_key}"
        response = requests.get(url)
        data = response.json()

        # Pogoda
        weather = data.get("weather", [{}])[0].get("main", "").lower()

        # Godzina lokalna
        timestamp_utc = datetime.utcnow()
        timezone_offset = data.get("timezone", 0)  # sekundy
        local_time = timestamp_utc.timestamp() + timezone_offset
        hour = datetime.fromtimestamp(local_time).hour

        # Czy jest dzień? (6–18)
        is_daytime = 6 <= hour < 18

        # Bazowe lx w zależności od pogody
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

        # Jeśli noc, drastycznie obniżamy natężenie światła
        if not is_daytime:
            base_light *= 0.01  # np. 1% z dziennego natężenia

        self.last_value = round(min(max(base_light, self.min_value), self.max_value), 2)

        # zapis do logu
        if self.logger:
            timestamp = datetime.now()
            self.logger.log_reading(self.sensor_id, timestamp, self.last_value, self.unit)

        # data
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] Odczyt natężenia światła ({self.name}): {self.last_value} {self.unit}")
        return self.last_value
