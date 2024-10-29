from HeaterManager import HeaterManager
import ujson
if __name__ == "__main__":
    #Import Json file
    config = ujson.load(open('heater_config.json', 'r'))
    mgr = HeaterManager(config)
    mgr.run()