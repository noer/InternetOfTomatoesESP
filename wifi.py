import network

class Wifi:
    def __init__(self, ssid, psk):
        station = network.WLAN(network.STA_IF)

        station.active(True)
        station.connect(ssid, psk)

        while not station.isconnected():
            pass

        ifcfg = station.ifconfig()
        print("WiFi started, IP:", ifcfg[0])
