from .reset_manager import ResetManager

class MazeResetManager(ResetManager):
    def __init__(self, reset_manager_name:str):
        super().__init__()
        self.__name = reset_manager_name
        self.__set_command = 'RESET_{}'.format(self.__name)

    @property
    def set_command(self):
        return self.__set_command

    def perform_reset(self, settings=None):
        return self.__set_command
        