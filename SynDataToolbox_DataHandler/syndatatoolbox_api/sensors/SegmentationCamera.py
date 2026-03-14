import math
import os
import cv2
import numpy as np
import seaborn as sns #for color palette
from .sensor import Sensor
from pathlib import Path

np.set_printoptions(threshold=np.inf)

#part of SegmentationCamera is inspired by RGBCamera

class SegmentationCamera(Sensor):

	def __init__(self,name,buffer_size,stringifyied_setup_dict:str,params_from_environment:dict=None):
		super().__init__()

		self.__formats:list = ['.mat','.npy','.png','.csv'] #supported format for mask file. By default
		
		if params_from_environment is None:
			params_from_environment = {
				"show":False,
				"mask_folder_path": None,
				"mask_colorized":None,
				"format_output_mask":None,
				"segmentation_video_path":None
			}

		self.__show = None
		if params_from_environment['show'] is not None and params_from_environment['show'] != "None":
			self.__show = params_from_environment['show']
		
		self.__mask_folder_path = None
		if params_from_environment['mask_folder_path'] is not None and params_from_environment['mask_folder_path'] != "None":
			self.__mask_folder_path = params_from_environment['mask_folder_path']
		
		self.__format_output_mask = None
		if params_from_environment['format_output_mask'] is not None and params_from_environment['format_output_mask'] != "None":
			if params_from_environment['format_output_mask'] in self.__formats:
				self.__format_output_mask= params_from_environment['format_output_mask']
			else:
				self.__format_output_mask= '.png'

		self.__mask_colorized = None
		if params_from_environment['mask_colorized'] is not None and params_from_environment['mask_colorized'] != "None":
			if params_from_environment['mask_colorized'] in ['RGB','GRAYSCALE']:
				self.__mask_colorized = params_from_environment['mask_colorized']
			else:
				self.__mask_colorized = 'GRAYSCALE'

		self.__segmentation_video_path = None
		if params_from_environment['segmentation_video_path'] is not None and params_from_environment['segmentation_video_path'] != "None":
				self.__segmentation_video_path = params_from_environment['segmentation_video_path']

		self.video = None
		self.idx = 0

		self.__buffer_size = buffer_size
		self.__name = name
		self.__settings_sensor = self.parse_dict(stringifyied_setup_dict)
		self.__command = 'OBS_{}'.format(self.__name)
		self.__color_palette = None #list of tuples: if channels == RGB, define for each class of object a specific RGB Color
		
		if self.__mask_colorized == 'RGB':
			i =0
			self.__dict_values = dict()
			for value in list(self.__settings_sensor['Classes'].values()):
				self.__dict_values[value] = i
				i+=1
			self.__color_palette = sns.diverging_palette(255, 133, l=60, center="light",n=i)
		# self.change_settings(width, height, channels, FOV, object_to_find,focal, show, mask_folder_path,format_output_mask,video_path)


		id_r = np.random.randint(0, 1000, size=1)
		pid = os.getpid()
		self.__identification = 'PID:'+str(pid)+str(id_r)

	@property
	def name(self):
		return self.__name

	@property
	def change_command(self):
		return self.__change_command

	@property
	def buffer_size(self):
		return self.__buffer_size

	@buffer_size.setter
	def buffer_size(self,value):
		self.__buffer_size = value


	@property
	def command(self):
		return self.__command

	@property
	def settings(self):
		return self.__settings_sensor

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
			if self.__mask_colorized == 'RGB':
				i = 1
				self.__dict_values = dict()
				self.__dict_values[0] = 0
				for value in list(self.__settings_sensor['Classes'].values()):
					self.__dict_values[value] = i
					i+=1
				self.__color_palette = sns.diverging_palette(255, 133, l=60, center="light",n=i)

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

	def get_observation(self, data):
		if self.__settings_sensor['InstanceSegmentation'] == 0:
			mask = np.frombuffer(data, dtype=np.uint8).reshape(self.__settings_sensor['Height'], self.__settings_sensor['Width']).astype(np.uint8)
		else:
			aux = np.frombuffer(data, dtype=np.uint8).reshape(self.__settings_sensor['Height'], 
			self.__settings_sensor['Width'], 2).astype(np.uint8)
			mask = np.zeros((self.__settings_sensor['Height'],self.__settings_sensor['Width'],3))
			mask[:,:,:2] = aux 

		# with respect to RGBCamera, "cpp" sends a grayscale image (a matrix), where the value of i,jth pixel is one of class indexes 
		image_formatted = mask
		if self.__show or self.__mask_folder_path or self.__segmentation_video_path:
			if self.__show is True:
				if self.__mask_colorized == 'RGB':
					colorized = self.__format_image(mask) #colorize mask
					self.__show_image_on_screen(RGB_image_formatted=colorized)
				else:
					self.__show_image_on_screen(RGB_image_formatted=image_formatted)
			if self.__mask_folder_path is not None:
				self.__save_mask(mask=image_formatted)
			if self.__segmentation_video_path is not None:
				if self.__mask_colorized == 'RGB':
					image_formatted = self.__format_image(mask)
				self.__save_video(image_formatted)
		return mask

	def __format_image(self, mask):
		#given mask matrix, map each value (from 0 to 255) to a specific color class
		rgb_mask = np.zeros(shape=(mask.shape[0],mask.shape[1],3)) 
		for i in range(rgb_mask.shape[0]):
			for j in range(rgb_mask.shape[1]):
				if self.__settings_sensor['InstanceSegmentation'] == 1:
					class_index = int(mask[i,j,0])
					rgb_mask[i,j,:] = list(self.__color_palette[self.__dict_values[class_index]])
					if class_index != 0:
						rgb_mask[i,j,1] += mask[i,j,1]#increment green channel
				else:
					rgb_mask[i,j,:] = list(self.__color_palette[self.__dict_values[int(mask[i,j])]])
		return rgb_mask

	def __show_image_on_screen(self, RGB_image_formatted):
		image = RGB_image_formatted[...,::-1]
		cv2.imshow('{}_{}_{}'.format(self.__name, ''.join(sorted(set('RGB'), key='RGB'.index)), self.__identification), image)
		cv2.waitKey(1)

	def __save_image(self, image_formatted):
		if self.__settings_sensor['InstanceSegmentation'] == 0:
			if self.__mask_colorized == 'RGB':
				cv2.imwrite('{}/mask_{}.png'.format(self.__mask_folder_path, str(self.idx).zfill(6)), (image_formatted * 255).astype(np.uint8))
			else: #grayscale
				cv2.imwrite('{}/mask_{}.png'.format(self.__mask_folder_path, str(self.idx).zfill(6)), (image_formatted).astype(np.uint8))
		else:
			mask = np.zeros_like(image_formatted)
			mask = image_formatted[...,::-1]
			if self.__mask_colorized == 'RGB':
				cv2.imwrite('{}/mask_{}.png'.format(self.__mask_folder_path, str(self.idx).zfill(6)), (mask*255).astype(np.uint8))
			else:
				cv2.imwrite('{}/mask_{}.png'.format(self.__mask_folder_path, str(self.idx).zfill(6)), (mask).astype(np.uint8))
	
		self.idx += 1

	def __save_video(self, RGB_image_formatted):
		if self.__mask_colorized == 'RGB':
			self.video.write((RGB_image_formatted * 255).astype(np.uint8))	
		else:
			self.video.write((RGB_image_formatted).astype(np.uint8))	

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

	def __save_mask(self,mask:np.ndarray):
		if (self.__format_output_mask == '.png' ):
			if(self.__settings_sensor['InstanceSegmentation'] == 0):
				if(self.__mask_colorized == 'RGB' and len(mask.shape) == 2):
					colorized = self.__format_image(mask) #colorized
					self.__save_image(colorized)
				elif(self.__mask_colorized == 'Grayscale' and len(mask.shape) == 3):
					# mask = self.__restore_image(mask) #restore image
					self.__save_image(mask) #grayscale
				else:
					self.__save_image(mask) #grayscale
			else:
				if(self.__mask_colorized == 'RGB'):
					colorized = self.__format_image(mask)
					self.__save_image(colorized)
				else:
					self.__save_image(mask)	
		elif(self.__format_output_mask in self.__formats ):
			filename = Path(f"{self.__mask_folder_path}/mask_{str(self.idx).zfill(6)}{self.__format_output_mask}")
			filename.touch(exist_ok=True)  # will create file, if it exists will do nothing

			with open(filename,"wb") as f:
				if(self.__format_output_mask == '.csv'):
					np.savetxt(f,mask,delimiter=",",fmt="%u") #special syntax for csv
				else:
					np.save(f,mask) #other binary format
		else:
			raise TypeError("save_mask exception: unsupported format. Choose between .png .npy .mat .csv")		

		self.idx+=1

	def close(self):
		if self.video is not None:
			self.video.release()
		cv2.destroyAllWindows()
