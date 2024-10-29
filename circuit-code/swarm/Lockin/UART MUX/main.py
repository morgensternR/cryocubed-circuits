from LockinManager import LockinManager
import ujson

if __name__ == "__main__":
    #Import Json file
    config = ujson.load(open('lockin_config.json', 'r'))
    mgr = LockinManager(config)
    mgr.run()