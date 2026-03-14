from .sensor import Sensor
import numpy as np


class GPS(Sensor):

	def __init__(self, name, buffer_size,params_from_environment:str,stringifyed_setup_dict:str):
		super().__init__()
		self.__name = name
		self.__buffer_size = buffer_size
		self.__command = 'OBS_{}'.format(self.__name)
		self.__settings_sensor = {}


	@property
	def change_command(self):
		return self.__change_command

	@property
	def command(self):
		return self.__command
	
	@property
	def name(self):
		return self.__name
    
	@property
	def buffer_size(self):
		return self.__buffer_size
	
	@buffer_size.setter
	def buffer_size(self,value):
		self.__buffer_size = value

	@property
	def settings(self):
		return self.__settings_sensor

	def get_observation(self, data):
		GPS_info = np.frombuffer(data, dtype=np.float32)
		GPS_info[1] *= -1
		GPS_info[4] *= -1
		GPS_info[7] *= -1
		GPS_info[10] *= -1
		return GPS_info

	def change_settings(self):
		self.__change_command = 'CHANGE_{}'.format(self.__name)

	def close(self):
		pass
