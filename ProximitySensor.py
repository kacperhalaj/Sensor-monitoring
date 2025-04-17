import random
from datetime import datetime
from sensor import Sensor

class ProximitySensor(Sensor):
    def read_value(self):
        if not self.active:
            raise Exception(f"Czujnik {self.name} jest wyłączony.")

        distance = round(random.uniform(self.min_value, self.max_value), 2)
        self.last_value = distance

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] Odczyt zbliżeniowy ({self.name}): {self.last_value} {self.unit}")
        return self.last_value
