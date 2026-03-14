from .sensor import Sensor
import numpy as np

class CollisionDetector(Sensor):
    
    def __init__(self,name, buffer_size, stringifyied_setup_dict:str, params_from_environment:dict):
        super().__init__()
        self.__name = name
        self.__buffer_size = buffer_size
        
        if params_from_environment is None:
            params_from_environment = {'show':False}

        self.__show = None
        if params_from_environment['show'] is not None and params_from_environment['show'] != "None":
            self.__show = params_from_environment["show"]  
        
        self.__command = 'OBS_{}'.format(self.__name)
        self.__change_command = None

		# self.__identification = 'PID:'+str(pid)+str(id_r)
        self.__settings_sensor = self.parse_dict(stringifyied_setup_dict)

    
    @property
    def settings(self):
        return self.__settings_sensor

    @property
    def name(self):
        return self.name

    @property
    def buffer_size(self):
        return self.__buffer_size

    @buffer_size.setter
    def buffer_size(self,value):
        self.__buffer_size = value

    @property
    def change_command(self):
        return self.__change_command

    @property
    def command(self):
        return self.__command

    @property
    def setup(self):
        return self.__settings_sensor

    def change_settings(self, PawnAgent=None, ActorTarget=None):
        # for now, is unavailable the change of reference!
        pass

    def get_observation(self, data):
        result = np.frombuffer(data, dtype=np.uint8)

        # if self.__show and result[0] == 1:
        #     print('Collision detected!')
        return result

    def close(self):
        pass