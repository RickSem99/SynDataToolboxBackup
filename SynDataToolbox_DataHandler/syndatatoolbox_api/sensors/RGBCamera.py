from .sensor import Sensor
import numpy as np
import math
import cv2
import os


np.set_printoptions(threshold=np.inf)


class RGBCamera(Sensor):

	def __init__(self,name, buffer_size, stringifyied_setup_dict:str, params_from_environment:dict=None):
		super().__init__()
		self.__name = name
		self.__channels = 'RGB'
		self.__channel_list = []
		channel_dict = {'R': 0, 'G': 1, 'B': 2, 'D': 3}
		for c in self.__channels:
			c_n = channel_dict[c]
			self.__channel_list.append(c_n)
		self.idx = 0
		
		self.__settings_sensor = self.parse_dict(stringifyied_setup_dict)

		if params_from_environment is None:
			params_from_environment = {"show": False, "image_folder_path": None, "video_path": None}
		
		self.__show = None
		if params_from_environment['show'] is not None and params_from_environment['show'] != "None":
			self.__show = params_from_environment["show"]
		
		self.__image_folder_path = None
		if params_from_environment['image_folder_path'] is not None and params_from_environment['image_folder_path'] != "None":
			self.__image_folder_path = params_from_environment["image_folder_path"]
		
		self.__video_path = None
		self.video = None
		if params_from_environment['video_path'] is not None and params_from_environment['video_path'] != "None":
			self.__video_path = params_from_environment["video_path"]
			self.video = cv2.VideoWriter(f"self.__video_path_{name}.mp4", cv2.VideoWriter_fourcc(*'DIVX'), 25, (self.__settings_sensor['Width'], self.__settings_sensor['Height']))

		self.__num_channels = 3
		self.__buffer_size = buffer_size

		id_r = np.random.randint(0, 1000, size=1)
		pid = os.getpid()
		
		self.__command = 'OBS_{}'.format(self.__name)
		self.__change_command = None

		self.__identification = 'PID:'+str(pid)+str(id_r)

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

	def change_settings(self, Width=None, Height=None, FOV=None, focal=None):
		if Width is not None:
			self.__settings_sensor['Width'] = Width
			self.__settings_sensor['cx'] = Width / 2
		if Height is not None:
			self.__settings_sensor['Height'] = Height
			self.__settings_sensor['cy'] = Height / 2
		if FOV is not None:
			self.__settings_sensor['FOV'] = FOV
			self.__settings_sensor['focal'] = 0.5 * self.__settings_sensor['Width'] / math.tan(0.5 * math.radians(self.__settings_sensor['FOV']))
		elif focal is not None:
			self.__settings_sensor['focal'] = focal
			self.__settings_sensor['FOV'] = math.degrees(2 * math.atan(self.__settings_sensor['Width'] / (2 * self.__settings_sensor['focal'])))
		camera_matrix = [[self.__settings_sensor['focal'], 0, self.__settings_sensor['cx']], [0, self.__settings_sensor['focal'], self.__settings_sensor['cy']], [0, 0, 1]]
		self.__settings_sensor['camera_matrix'] = np.array(camera_matrix)

		self.__change_command = 'CHANGE_{}_{}_{}_{}'.format(self.__name, self.__settings_sensor['Width'], self.__settings_sensor['Height'], self.__settings_sensor['FOV'])

	def get_observation(self, data):
		image = np.frombuffer(data, dtype=np.uint8).reshape(self.__settings_sensor['Height'], self.__settings_sensor['Width'], self.__num_channels).astype(np.float32) / 255
		RGB_image = image[:, :, :3]

		if self.__show or self.__image_folder_path or self.__video_path:
			RGB_image_formatted = self.__format_image(RGB_image)
			if self.__show:
				self.__show_image_on_screen(RGB_image_formatted)
			if self.__image_folder_path is not None:
				self.__save_image(RGB_image_formatted)
			if self.__video_path is not None:
				self.__save_video(RGB_image_formatted)

		return RGB_image

	def __format_image(self, RGB_image):
		rgb_list = list(set(self.__channel_list) & {0, 1, 2})
		if rgb_list:
			RGB_image_to_show = np.zeros_like(RGB_image)
			for c_n in rgb_list:
				RGB_image_to_show[:, :, c_n] = RGB_image[:, :, c_n]

			return RGB_image_to_show[..., ::-1]

	def __show_image_on_screen(self, RGB_image_formatted):
		cv2.imshow('{}_{}_{}'.format(self.__name, ''.join(sorted(set('RGB') & set(self.__channels), key='RGB'.index)), self.__identification), RGB_image_formatted)
		cv2.waitKey(1)

	def __save_image(self, RGB_image_formatted):
		cv2.imwrite('{}{}.png'.format(self.__image_folder_path, str(self.idx).zfill(6)), (RGB_image_formatted * 255).astype(np.uint8))
		self.idx += 1

	def __save_video(self, RGB_image_formatted):
		self.video.write((RGB_image_formatted * 255).astype(np.uint8))

	def close(self):
		if self.video is not None:
			self.video.release()
		cv2.destroyAllWindows()