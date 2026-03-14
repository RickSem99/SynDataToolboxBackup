from abc import ABCMeta, abstractmethod


class ActionManager(metaclass=ABCMeta):

	@property
	@abstractmethod
	def set_command(self):
		pass

	@property
	@abstractmethod
	def action_set(self):
		pass

	@property
	@abstractmethod
	def name(self):
		pass

	@property
	@abstractmethod
	def settings(self):
		pass

	@abstractmethod
	def __init__(self):
		pass

	@abstractmethod
	def get_number_of_actions(self):
		pass

	@abstractmethod
	def perform_action(self, val):
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
