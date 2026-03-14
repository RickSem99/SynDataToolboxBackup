from .sensor import Sensor
import numpy as np
import math
import cv2
import json


class Lidar(Sensor):

	def __init__(self,name, buffer_size, stringifyied_setup_dict:str, params_from_environment:dict=None):
		super().__init__()
		self.__name = name
		self.__buffer_size = buffer_size
		self.__command = 'OBS_{}'.format(self.__name)

		self.__settings_sensor = self.parse_dict(stringifyied_setup_dict)

		self.__show = None
		if params_from_environment['show'] is not None and params_from_environment['show'] != "None":
			self.__show = params_from_environment['show']

		self.__x_rays = int((self.__settings_sensor['EndAngleX'] - self.__settings_sensor['StartAngleX']) / self.__settings_sensor['DistanceAngleX'] + 1)
		self.__y_rays = int((self.__settings_sensor['EndAngleY'] - self.__settings_sensor['StartAngleY']) / self.__settings_sensor['DistanceAngleY'] + 1)

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
	def change_command(self):
		return self.__change_command

	@property
	def command(self):
		return self.__command

	@property
	def settings(self):
		return self.__settings_sensor

	def get_observation(self, data):
		lidar_vector = np.frombuffer(data, dtype=np.float32).reshape(self.__y_rays, self.__x_rays, 3)
		lidar_vector[:, :, 1] *= -1
		if self.__show:
			self.__show_laser_on_screen(lidar_vector)
		return lidar_vector

	def change_settings(self, start_angle_x=None, end_angle_x=None, distance_angle_x=None, start_angle_y=None, end_angle_y=None, distance_angle_y=None, laser_range=None, show=None, Render=None):
		if start_angle_x is not None:
			self.__settings_sensor['StartAngleX'] = start_angle_x
		if end_angle_x is not None:
			self.__settings_sensor['EndAngleX'] = end_angle_x
		if distance_angle_x is not None:
			self.__settings_sensor['DistanceAngleX'] = distance_angle_x
		if start_angle_y is not None:
			self.__settings_sensor['StartAngleY'] = start_angle_y
		if end_angle_y is not None:
			self.__settings_sensor['EndAngleY'] = end_angle_y
		if distance_angle_y is not None:
			self.__settings_sensor['DistanceAngleY'] = distance_angle_y
		if laser_range is not None:
			self.__settings_sensor['LaserRange'] = laser_range
		if show is not None:
			self.__show = show
		if Render is not None:
			self.__settings_sensor['Render'] = Render

		self.__x_rays = int((self.__settings_sensor['EndAngleX'] - self.__settings_sensor['StartAngleX']) / self.__settings_sensor['DistanceAngleX'] + 1)
		self.__y_rays = int((self.__settings_sensor['EndAngleY'] - self.__settings_sensor['StartAngleY']) / self.__settings_sensor['DistanceAngleY'] + 1)

		self.__change_command = 'CHANGE_{}_{}_{}_{}_{}_{}_{}_{}_{}'.format(self.__name, self.__settings_sensor['StartAngleX'], self.__settings_sensor['EndAngleX'], self.__settings_sensor['DistanceAngleX'], self.__settings_sensor['StartAngleY'], self.__settings_sensor['EndAngleY'], self.__settings_sensor['DistanceAngleY'], self.__settings_sensor['LaserRange'], self.__settings_sensor['Render'])

	def __show_laser_on_screen(self, laser_vector):
		resized = cv2.resize(laser_vector, (self.__x_rays * 3, self.__y_rays * 3), interpolation=cv2.INTER_AREA)
		cv2.imshow(self.__name, resized)
		cv2.waitKey(1)
	
	def close(self):
		cv2.destroyAllWindows()
