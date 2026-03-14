from abc import ABCMeta, abstractmethod

class Sensor(metaclass=ABCMeta):
	
	@property
	@abstractmethod
	def change_command(self):
		pass

	@property
	@abstractmethod
	def name(self):
		pass

	@property
	@abstractmethod
	def command(self):
		pass

	@property
	@abstractmethod
	def settings(self):
		pass

	@abstractmethod
	def __init__(self):
		pass
 
	@abstractmethod
	def change_settings(self):
		pass

	@abstractmethod
	def get_observation(self, data):
		pass
	
	@property
	@abstractmethod
	def buffer_size(self):
		pass
	
	@buffer_size.setter
	def buffer_size(self, value):
		pass

	@abstractmethod
	def close(self):
		pass
	
	
	def parse_dict(self, stringifyied_setup_dict:str):
		setup_dict = dict()
		aux_str = stringifyied_setup_dict[1:-1]

		if aux_str == "":
			return setup_dict

		j=-1
		tokens = aux_str.split(",")
		for index,kvp in enumerate(tokens):
			if index>j:
				#elements included in recursive call
				key,value = kvp.split(":",1)
				if((value[0] != "{")):				
					try:
						value = float(value) #raise exception if value is a string
						if value.is_integer():
							setup_dict[key] = int(value)
						else:
							setup_dict[key] = value
					except ValueError:
						setup_dict[key] = value
				else:
					toBeParsed = ""
					if(value[-1]=="}"):
						# dict with only one element
						toBeParsed = value
					else:
						# dict with more than one element
						j=index+1
						toBeParsed=value+","
						while(tokens[j][-1] != "}"):
							j+=1
						toBeParsed+= ",".join(tokens[index+1:j+1])
					# recursive ahah
					setup_dict[key] = self.parse_dict(toBeParsed)
					
		return setup_dict
