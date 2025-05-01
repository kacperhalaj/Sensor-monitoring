import random
from datetime import datetime
from sensor import Sensor

class AccelerometerSensor(Sensor):
    def __init__(self, sensor_id, name, unit, min_value, max_value, logger=None):
        super().__init__(sensor_id, name, unit, min_value, max_value)
        self.logger = logger

    def read_value(self):
        if not self.active:
            raise Exception(f"Czujnik {self.name} jest wyłączony.")

        x = round(random.uniform(self.min_value, self.max_value), 2)
        y = round(random.uniform(self.min_value, self.max_value), 2)
        z = round(random.uniform(self.min_value, self.max_value), 2)
        self.last_value = (x, y, z)

        # zapis do logu
        if self.logger:
            timestamp = datetime.now()
            self.logger.log_reading(self.sensor_id, timestamp, self.last_value, self.unit)

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] Odczyt akcelerometru ({self.name}): X={x}g, Y={y}g, Z={z}g")
        return self.last_value
