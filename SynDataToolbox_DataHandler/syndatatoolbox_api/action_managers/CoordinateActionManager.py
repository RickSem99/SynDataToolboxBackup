from .action_manager import ActionManager


class CoordinateActionManager(ActionManager):

	def __init__(self, action_manager_name,action_manager_commands:str,action_manager_setup:str):
		super().__init__()
		self.__name = action_manager_name
		self.__action_set = action_manager_commands.split(",")

		if action_manager_setup=="{}":
			self.__settings = dict()
		else:
			self.__settings = self.parse_dict(action_manager_setup)

	@property
	def set_command(self):
		return self.__set_command

	@property
	def name(self):
		return self.__name

	@property
	def action_set(self):
		return self.__action_set

	@property
	def settings(self):
		return self.__settings

	def get_number_of_actions(self):
		return len(self.__action_set)


	def perform_action(self, operation_obj:dict):
		command = f'ACTION_{self.__name}_'
		action_op = list(operation_obj.keys())[0]
		value_op = list(operation_obj.values())[0]
		if type(value_op) is not list:
			print("Error, value of given operation must be a list of 6 integer")
			return ""
		try:
			self.__action_set.index(action_op)
			if value_op is not None:
				command += action_op
				for v in range(len(value_op)):
					command += ";{:.8f}".format(value_op[v])
				command += "_"
		except ValueError:
			print(f"ERROR: COMMAND {action_op} FOR {self.__name} IS NOT DEFINED!")
			print(f"Available actions for {self.__name} are: {self.__action_set}")
			return ""

		return command[:-1]
