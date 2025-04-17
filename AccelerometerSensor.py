import random
from datetime import datetime
from sensor import Sensor

class AccelerometerSensor(Sensor):
    def read_value(self):
        if not self.active:
            raise Exception(f"Czujnik {self.name} jest wyłączony.")

        x = round(random.uniform(self.min_value, self.max_value), 2)
        y = round(random.uniform(self.min_value, self.max_value), 2)
        z = round(random.uniform(self.min_value, self.max_value), 2)
        self.last_value = (x, y, z)

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] Odczyt akcelerometru ({self.name}): X={x}g, Y={y}g, Z={z}g")
        return self.last_value
