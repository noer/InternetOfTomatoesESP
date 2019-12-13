# Complete project details at https://RandomNerdTutorials.com

# Boot section
from config import Config
import utime as time
from umqttsimple import MQTTClient
import ubinascii
import machine
import micropython
import network
import esp
import gc
esp.osdebug(None)
gc.collect()

# EXAMPLE IP ADDRESS
# mqtt_server = '192.168.1.144'
client_id = ubinascii.hexlify(machine.unique_id())
topic_led = b'/control/3/led'
topic_sensor = b'/sensor/air'

last_message = 0
message_interval = 5
counter = 0

import wifi
wifinet = wifi.Wifi(Config.wifi_ssid, Config.wifi_password)


from machine import RTC
import ntptime
rtc = RTC()
try:
    ntptime.settime()
except OSError as e:
    pass
print(rtc.datetime())


from dht import DHT22
from machine import Pin, PWM
import json
sensor = DHT22(Pin(2))

led_value = 0
led = PWM(Pin(4), freq=1000)


# MAIN Program
def set_led(value):
    global led, led_value
    fade(led_value, value)
    led_value = value


def fade(fade_from, fade_to):
    global led
    step = 1
    if fade_from > fade_to:
        step = -1
    for i in range(fade_from, fade_to, step):
        led.duty(i * 10)
        time.sleep_ms(20)


def sub_cb(topic, msg):
    print((topic, msg))
    if topic == topic_led:
        print('ESP received hello message: ' + str(msg))
        set_led(int(msg))


def connect_and_subscribe():
    global client_id, topic_led
    client = MQTTClient(client_id, Config.mqtt_server, user=Config.mqtt_user, password=Config.mqtt_pass)
    client.set_callback(sub_cb)
    client.connect(clean_session=False)
    client.subscribe(topic_led)
    return client


def restart_and_reconnect():
    print('Failed to connect to MQTT broker. Reconnecting...')
    time.sleep(10)
    machine.reset()


# Generate Sensor-data message
def gen_json_message(name, value):
    data = {
        'id': Config.ID,
        'timestamp': time.time()+946684800,
        'name': name,
        'value': value
    }
    return json.dumps(data)


try:
    mqtt_client = connect_and_subscribe()

    while True:
        mqtt_client.check_msg()
        # Then need to sleep to avoid 100% CPU usage (in a real
        # app other useful actions would be performed instead)
        time.sleep(1)

        if time.time() % 30 == 0:
            sensor.measure()   # Poll sensor
            t = sensor.temperature()
            if isinstance(t, float):  # Confirm sensor results are numeric
                mqtt_client.publish(topic_sensor, gen_json_message('temperature', t))
            h = sensor.humidity()
            if isinstance(h, float):  # Confirm sensor results are numeric
                mqtt_client.publish(topic_sensor, gen_json_message('humidity', h))

        if time.time() % 300 == 0:
            try:
                ntptime.settime()
            except OSError as e:
                pass


except OSError as e:
    restart_and_reconnect()
