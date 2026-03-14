from .sensor import Sensor
import numpy as np
import json
import math 
class BoundingBox(Sensor):

	def __init__(self, name, buffer_size,stringifyied_setup_dict:str, params_from_environment:dict=None):
		super().__init__()
		self.__name = name
		self.__command = 'OBS_{}'.format(self.name)
		self.__buffer_size = buffer_size
		self.__bounding_box_file_path = None
		self.idx = 0
		self.__bounding_box_file_path = None
		self.__print_output = False

		if params_from_environment['bounding_box_file_path'] is not None and params_from_environment['bounding_box_file_path'] != "None":
			self.__bounding_box_file_path = params_from_environment['bounding_box_file_path']

		if params_from_environment['bounding_box_print_output'] is not None and params_from_environment['bounding_box_print_output'] != "None":
			self.__print_output = params_from_environment['bounding_box_print_output']

		self.__settings_sensor = self.parse_dict(stringifyied_setup_dict=stringifyied_setup_dict)
		


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
		BBox_info = np.frombuffer(data, dtype=np.uint8)
		bounding_boxes = self.__parse_coordinates(np.array_split(BBox_info,self.__settings_sensor['MaxActors']))
		if self.__print_output:
			print(bounding_boxes)
		if self.__bounding_box_file_path is not None:
			self.__save_observation(bounding_boxes=bounding_boxes)
	
	
	def change_settings(self, Width=None, Height=None, FOV=None, Classes:dict=None, focal=None):
		short_command = False
		if [FOV, focal].count(None) == 0:
			raise TypeError("Exactly 1 between the FOV and the focal must be specified.")

		if Width is not None:
			self.__settings_sensor['Width'] = Width
			self.__settings_sensor['cx'] = Width / 2
		if Height is not None:
			self.__settings_sensor['Height'] = Height
			self.__settings_sensor['cy'] = Height / 2
		if Classes is not None:
			if self.__check_dict_syntax(Classes):
				self.__settings_sensor['Classes']= Classes
				# self.__list_values.extend(list(self.__settings_sensor['Classes'].values()))
		else:
			short_command = True
		if FOV is not None:
			self.__settings_sensor['FOV'] = FOV
			self.__settings_sensor['focal'] = 0.5 * self.__settings_sensor['Width'] / math.tan(0.5 * math.radians(self.__settings_sensor['FOV']))
		elif focal is not None:
			self.__settings_sensor['focal'] = focal
			self.__settings_sensor['FOV'] = math.degrees(2 * math.atan(self.__settings_sensor['Width'] / (2 * self.__settings_sensor['focal'])))
		camera_matrix = [[self.__settings_sensor['focal'], 0, self.__settings_sensor['cx']], [0, self.__settings_sensor['focal'], self.__settings_sensor['cy']], [0, 0, 1]]
		self.__settings_sensor['camera_matrix'] = np.array(camera_matrix)


		if short_command:
			self.__change_command = 'CHANGE_{}_{}_{}_{}'.format(self.__name, self.__settings_sensor['Width'], self.__settings_sensor['Height'], self.__settings_sensor['FOV'])
		else:
			self.__change_command = 'CHANGE_{}_{}_{}_{}_{}'.format(self.__name, self.__settings_sensor['Width'], self.__settings_sensor['Height'], self.__settings_sensor['FOV'], self.__dict_to_str(self.__settings_sensor['Classes']))


	def __save_observation(self,bounding_boxes:dict):
		with open(f'{self.__bounding_box_file_path}/bboxes_{self.idx}.json', 'w') as f:
			json.dump(bounding_boxes, f, indent=2)
			self.idx+=1

	def __parse_coordinates(self,list_of_token:list)->dict:
		# list_of_token is an array of 10-bytes chunks
		BoundingBoxes = dict()
		classes = self.__settings_sensor['Classes']
		for names in classes.keys():
			BoundingBoxes[names] = dict()
		classes_values = list(classes.values())
		classes_keys = list(classes.keys())
		for chunk in list_of_token:
			if(chunk[0] != 0):
				# because class 0 is unavailable
				class_value = int(chunk[0])
				class_instance =int(chunk[1])
				coord = list()
				if(chunk[3] != 0):
					x1 = np.uint16(chunk[3] << 8) | chunk[2]
					coord.append(int(x1))
				else:
					coord.append(int(chunk[2]))
				if(chunk[5] != 0):
					y1 = np.uint16(chunk[5] << 8) | chunk[4]
					coord.append(int(y1))
				else:
					coord.append(int(chunk[4]))
				if(chunk[7] != 0):
					x2 = np.uint16(chunk[7] << 8) | chunk[6]
					coord.append(int(x2))
				else:
					coord.append(int(chunk[6]))
				if(chunk[9] != 0):
					y2 = np.uint16(chunk[9] << 8) | chunk[8]
					coord.append(int(y2))
				else:
					coord.append(int(chunk[8]))
				index = classes_values.index(class_value)
				BoundingBoxes[classes_keys[index]][class_instance] = coord
			else:
				break
		return BoundingBoxes
	
	def close(self):
		pass

	def __check_dict_syntax(self,object_to_find:dict):
		# check if class 0 is passed as argument
		# actually the segmentation mask is a "grayscale" image 
		if 0 in list(object_to_find.values()):
			raise TypeError("objectToFindException: 0 class is reserved. Change with another number between 1 and 255")

		#because _ is used by server for command separation. If user is going to use it for declare a class of objects, module will raise an exception  
		for el in list(object_to_find.keys()):
			if len(el.split("_")) > 1:
				raise TypeError("objectToFindException: _ character is reserved.")		
		return True
	
	def __dict_to_str(self, object_to_find:dict) -> str:
		# this string will be send to cpp socket
		result = ""
		i=1
		for key,value in object_to_find.items():
			if i!=1:
				result+=","
			result+=f"{key}:{value}"
			i+=1
		return result+""
