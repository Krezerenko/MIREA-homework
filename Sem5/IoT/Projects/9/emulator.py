import dataclasses
import random
import time

import paho.mqtt.client as mqtt
from datetime import datetime


@dataclasses.dataclass
class SensorData:
    timestamp: str
    humidity: float
    sound_level: float
    voltage: float

    def as_dict(self):
        return dataclasses.asdict(self)

    def __str__(self):
        return (f"[{self.timestamp[11:19]}] "
                f"Вл-ть: {self.humidity:5.1f}% | "
                f"Громкость: {self.sound_level:6.2f}dB | "
                f"Напряжение: {self.voltage:4.2f}V")


class MultiClientSensorEmulator:
    def __init__(self, broker_host, broker_port, client_id_s1, client_id_s2, username=None, password=None):
        self.broker_host = broker_host
        self.broker_port = broker_port

        self.client_s1 = mqtt.Client(client_id=client_id_s1)
        self.client_s1.on_connect = self.on_connect
        if username:
            self.client_s1.username_pw_set(username, password)

        self.client_s2 = mqtt.Client(client_id=client_id_s2)
        self.client_s2.on_connect = self.on_connect
        if username:
            self.client_s2.username_pw_set(username, password)

        self.sensor_readings = {
            'humidity': {'min': 30.0, 'max': 90.0, 'current': 45.0, 'trend': 0.2},
            'sound_level': {'min': 30.0, 'max': 95.0, 'current': 40.0, 'trend': 0.5},
            'voltage': {'min': 3.0, 'max': 5.0, 'current': 3.3, 'trend': -0.05}
        }

        self.mqtt_topics = {
            'humidity': "/devices/sensors/s1/humidity",
            'sound_level': "/devices/sensors/s2/sound level",
            'voltage': "/devices/sensors/s1/voltage"
        }

    def on_connect(self, client, userdata, flags, rc):
        client_id = client._client_id.decode('utf-8')
        if rc == 0:
            print(f"Клиент '{client_id}' успешно подключился к {self.broker_host}")
        else:
            print(f"Ошибка подключения клиента '{client_id}'. Код: {rc}")
            if rc == 5:
                print("-> Ошибка аутентификации: проверьте логин и пароль.")

    def update_sensor_readings(self):
        for sensor, params in self.sensor_readings.items():
            change = params['trend'] + random.uniform(-0.5, 0.5)
            params['current'] += change

            if params['current'] < params['min']:
                params['current'] = params['min']
                params['trend'] = abs(params['trend'])
            elif params['current'] > params['max']:
                params['current'] = params['max']
                params['trend'] = -abs(params['trend'])

            if random.random() < 0.1:
                params['trend'] = random.uniform(-1, 1)

    def generate_sensor_data(self) -> SensorData:
        self.update_sensor_readings()

        return SensorData(
            timestamp=datetime.now().isoformat(),
            humidity=round(self.sensor_readings['humidity']['current'], 1),
            sound_level=round(self.sensor_readings['sound_level']['current'], 2),
            voltage=round(self.sensor_readings['voltage']['current'], 2)
        )

    def publish(self, sensor_data: SensorData):
        self.client_s1.publish(self.mqtt_topics["humidity"], sensor_data.humidity)
        self.client_s1.publish(self.mqtt_topics["voltage"], sensor_data.voltage)

        self.client_s2.publish(self.mqtt_topics["sound_level"], sensor_data.sound_level)

        print(sensor_data)

    def start_emulation(self, interval):
        print("Запуск эмуляции датчиков...")
        try:
            self.client_s1.connect(self.broker_host, self.broker_port, 60)
            self.client_s2.connect(self.broker_host, self.broker_port, 60)

            self.client_s1.loop_start()
            self.client_s2.loop_start()

            while True:
                data = self.generate_sensor_data()
                self.publish(data)
                time.sleep(interval)

        except KeyboardInterrupt:
            print("\n\nЭмуляция остановлена пользователем.")
        except Exception as e:
            print(f"Произошла ошибка: {e}")
        finally:
            self.client_s1.loop_stop()
            self.client_s1.disconnect()
            self.client_s2.loop_stop()
            self.client_s2.disconnect()
            print("Соединения с MQTT брокером закрыты.")


if __name__ == "__main__":
    emulator = MultiClientSensorEmulator(
        broker_host="dev.rightech.io",
        broker_port=1883,
        client_id_s1="mqtt-mihakom050-s1",
        client_id_s2="mqtt-mihakom050-s2"
    )
    emulator.start_emulation(interval=10)
