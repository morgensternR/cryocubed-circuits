from DiodeSensorManager import DiodeSensorManager
import ujson

if __name__ == "__main__":
    config = ujson.load(open('diode_config.json', 'r'))
    mgr = DiodeSensorManager(config)
    mgr.run()
