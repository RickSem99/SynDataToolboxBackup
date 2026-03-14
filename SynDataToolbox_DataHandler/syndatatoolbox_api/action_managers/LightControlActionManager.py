from .action_manager import ActionManager


class LightControlActionManager(ActionManager):
    """
    Action Manager Python per il controllo delle luci in Unreal Engine.
    Supporta: SETCOLOR, SETINTENSITY, SETRADIUS, SETALL
    """

    def __init__(self, action_manager_name, action_manager_commands: str, action_manager_setup: str):
        super().__init__()
        self.__name = action_manager_name
        self.__action_set = action_manager_commands.split(",")

        if action_manager_setup == "{}":
            self.__settings = dict()
        else:
            self.__settings = self.parse_dict(action_manager_setup)

        self.__current_command = None  # nuovo attributo di supporto

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

    def perform_action(self, operation_obj: dict):
        """
        Genera il comando in formato Unreal:
        ACTION_LightControlActionManager(LightControlActionManagerSDT)_<AZIONE>;<parametri>_
        """
        command = f"ACTION_{self.__name}_"
        action_op = list(operation_obj.keys())[0]
        value_op = list(operation_obj.values())[0]

        # Validazione tipo base
        if not isinstance(value_op, list):
            print(f"❌ Error: value for {action_op} must be a list of floats")
            return ""

        expected_lengths = {
            "SETCOLOR": 3,
            "SETINTENSITY": 1,
            "SETRADIUS": 1,
            "SETALL": 5
        }

        if action_op in expected_lengths:
            expected = expected_lengths[action_op]
            if len(value_op) != expected:
                print(f"❌ ERROR: {action_op} requires {expected} parameters, got {len(value_op)}")
                return ""

        if action_op in ["SETCOLOR", "SETALL"]:
            for i in range(3):
                if not (0 <= value_op[i] <= 255):
                    print(f"⚠️ WARNING: RGB value at index {i} should be 0-255, got {value_op[i]}")

        # Costruzione comando
        if action_op not in self.__action_set:
            print(f"❌ ERROR: COMMAND {action_op} not defined! Available: {self.__action_set}")
            return ""

        command += f"{action_op};" + ";".join(f"{float(v):.8f}" for v in value_op) + "_"
        return command

    # 🔹 Metodo richiesto da ActionManager (necessario per non essere astratta)
    def set_command(self, command: str):
        """
        Implementazione richiesta dall'interfaccia ActionManager.
        Imposta un comando corrente (non sempre usato).
        """
        self.__current_command = command
