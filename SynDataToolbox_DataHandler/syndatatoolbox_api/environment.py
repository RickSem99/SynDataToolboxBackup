from .isar_socket import IsarSocket
import numpy as np
import importlib
import time
from typing import Tuple


class Environment:

    def __init__(self, port, address='localhost', render=False, fps=False, observations_step=None,
                 observations_reset=None, setup: dict = None):
        # type: ignore
        self.__port = port

        # La connessione IsarSocket gestisce il proprio timeout internamente.
        self.__sock = IsarSocket(port, address)

        # RIMOSSO IL BLOCCO TRY/EXCEPT SUL TIMEOUT CHE INTERFERIVA.

        self.setup = setup
        if setup is None:
            self.setup = {
                "show": True,
                "image_folder_path": None,
                "video_path": None,
                "format_output_mask": None,
                "mask_folder_path": None,
                "segmentation_video_path": None,
                "mask_colorized": None,  # 'RGB' or 'GRAYSCALE'
                "render": None,
            }

        self.__action_manager_set = self.__get_action_managers_set_from_UE4()
        self.__reset_manager_set = self.__get_reset_managers_set_from_UE4()
        self.__sensor_set = self.__get_sensors_from_UE4()

        if render:
            self.switch_rendering()
        if fps:
            self.enable_fps_counter()
        self.__observations_step = observations_step
        self.__observations_reset = observations_reset

    @property
    def port(self):
        return self.__port

    @property
    def action_manager_set(self):
        return self.__action_manager_set

    @property
    def action_set(self):
        # return self.__action_manager.action_set
        return self.__action_manager_set

    @property
    def sensor_set(self):
        return self.__sensor_set

    @property
    def observations_step(self):
        return self.__observations_step

    @property
    def sensor_dict(self):
        return self.sensor_dict

    @property
    def observations_reset(self):
        return self.__observations_reset

    def __get_sensors_from_UE4(self):
        sensor_dict = dict()
        self.__sock.send_command('SENSORS')
        sensor_list = self.__sock.rec_bytes(1)[0].decode("utf-8").split(' ')[:-1]
        print("-------------------------")
        print("Available sensors:")
        print("-------------------------")
        for sensor in sensor_list:
            sensor_name, sensor_other = sensor.split("#")
            print(f"\t{sensor_name}")
            sensor_buffer, sensor_setup = sensor_other.split("@")
            self.__append_sensor(sensor_name, np.uint32(sensor_buffer), sensor_setup, self.setup, sensor_dict)
        time.sleep(0.1)
        return sensor_dict

    def __get_action_managers_set_from_UE4(self):
        sensor_dict = dict()
        self.__sock.send_command('ACTIONS')
        action_manager_list = self.__sock.rec_bytes(1)[0].decode("utf-8").split(' ')[:-1]
        print("Available action managers:")
        print("-------------------------")
        for action_manager in action_manager_list:
            action_manager_name, action_manager_other = action_manager.split("#")
            print(f"\t{action_manager_name}")
            action_manager_commands, action_manager_setup = action_manager_other.split("@")
            self.__append_action_manager(action_manager_name, action_manager_commands,
                                         stringifyied_setup_dict=action_manager_setup, sensor_dict=sensor_dict)

        time.sleep(0.1)
        return sensor_dict

    def __get_reset_managers_set_from_UE4(self):
        sensor_dict = dict()
        self.__sock.send_command('RESETS')
        reset_manager_list = self.__sock.rec_bytes(1)[0].decode("utf-8").split(' ')[:-1]
        print("Available reset managers:")
        print("-------------------------")
        for reset_manager in reset_manager_list:
            reset_manager_name = reset_manager
            print(f"\t{reset_manager_name}")
            self.__append_reset_manager(reset_manager_name, sensor_dict=sensor_dict)
        time.sleep(0.1)
        return sensor_dict

    def __get_sensor(self, sensor_name):
        try:
            sensor = self.__sensor_set[sensor_name]
        except KeyError:
            self.close_connection()
            raise Exception('Invalid sensor.')
        if sensor is None:
            self.close_connection()
            raise Exception('{} has not been initialized.'.format(sensor_name))
        else:
            return sensor

    def __get_action_manager(self, action_manager_name):
        try:
            action_manager = self.__action_manager_set[action_manager_name]
        except KeyError:
            self.close_connection()
            raise Exception('Invalid action manager.')
        if action_manager is None:
            self.close_connection()
            raise Exception('{} not found.'.format(action_manager))
        else:
            return action_manager

    def __get_reset_manager(self, reset_manager_name):
        try:
            reset_manager = self.__reset_manager_set[reset_manager_name]
        except KeyError:
            self.close_connection()
            raise Exception('Invalid Reset manager.')
        if reset_manager is None:
            self.close_connection()
            raise Exception('{} not found.'.format(reset_manager))
        else:
            return reset_manager

    def __append_sensor(self, sensor_name: str, buffer_size: np.uint32, stringifyied_setup_dict: str, other_setup_info,
                        sensor_dict):
        sensor_class = sensor_name.split("(")[0]
        module = importlib.import_module('syndatatoolbox_api.sensors.{}'.format(sensor_class))
        class_ = getattr(module, sensor_class)
        instance = class_(sensor_name, buffer_size, stringifyied_setup_dict, other_setup_info)
        sensor_dict[sensor_name] = instance

    def __append_action_manager(self, action_manager_name: str, action_manager_commands: str,
                                stringifyied_setup_dict: str, sensor_dict: dict):
        # stringifyed_setup_dict could be empty! Now only discreteActionManager has setup!
        action_manager_class = action_manager_name.split("(")[0]
        module = importlib.import_module('syndatatoolbox_api.action_managers.{}'.format(action_manager_class))
        class_ = getattr(module, action_manager_class)
        instance = class_(action_manager_name, action_manager_commands, stringifyied_setup_dict)
        sensor_dict[action_manager_name] = instance

    def __append_reset_manager(self, reset_manager_name: str, sensor_dict: dict):
        reset_manager_class = reset_manager_name.split("(")[0]
        module = importlib.import_module('syndatatoolbox_api.reset_managers.{}'.format(reset_manager_class))
        class_ = getattr(module, reset_manager_class)
        instance = class_(reset_manager_name)
        sensor_dict[reset_manager_name] = instance

    def switch_rendering(self):
        self.__sock.send_command('RENDER')
        time.sleep(0.1)

    def enable_fps_counter(self):
        self.__sock.send_command('FPS')
        time.sleep(0.1)

    def change_sensor_settings(self, sensor_settings):
        sensor_change_command_list = []
        for sensor_name, settings in sensor_settings.items():
            sensor = self.__get_sensor(sensor_name)
            sensor.change_settings(**settings)
            sensor_change_command_list.append(sensor.change_command)

        self.__sock.send_command(' '.join(sensor_change_command_list))
        new_buffers_list = self.__sock.rec_bytes(len(list(sensor_settings.items())))

        for index, (sensor_name, _) in enumerate(sensor_settings.items()):
            sensor = self.__get_sensor(sensor_name=sensor_name)
            sensor.buffer_size = int(new_buffers_list[index].decode("utf-8"))

    def get_sensor_settings(self, sensor_name_list):
        sensor_settings_list = []
        for sensor_name in sensor_name_list:
            sensor = self.__get_sensor(sensor_name)
            sensor_settings_list.append(sensor.settings)
        return sensor_settings_list

    def reset(self, reset_manager_name: str, reset_settings=None):
        reset_manager = self.__get_reset_manager(reset_manager_name)
        command = reset_manager.perform_reset()
        self.__sock.send_command(command)
        data = self.__sock.rec_byte()
        done = np.frombuffer(data, dtype=np.uint8)
        return done

    def perform_action(self, action_manager_name: str, command_dict: dict):
        action_manager = self.__get_action_manager(action_manager_name)
        command = action_manager.perform_action(command_dict)
        self.__sock.send_command(command)
        data = self.__sock.rec_byte()
        hit = np.frombuffer(data, dtype=np.uint8)
        return hit

    def get_obs(self, sensor_name_list):
        sensor_list = []
        sensor_buffer_list = []
        sensor_command_list = []
        for sensor_name in sensor_name_list:
            sensor = self.__get_sensor(sensor_name)
            sensor_buffer_list.append(sensor.buffer_size)
            sensor_command_list.append(sensor.command)
            sensor_list.append(sensor)
        self.__sock.send_command(' '.join(sensor_command_list))
        data = self.__sock.rec_sensors_observations(sensor_buffer_list)
        obs_list = []
        for i in range(len(sensor_list)):
            obs_list.append(sensor_list[i].get_observation(data[i]))
        return obs_list

    def env_step(self, action_name_operation: dict, sensor_name_list: list):
        '''
        :param action_name_operation: dict with action manager name as key and action operation as value
        :param sensor_name_list: list of sensor names
        :return: hit, obs_list
        '''
        if sensor_name_list is None:
            sensor_name_list = self.__observations_step

        if type(sensor_name_list) is not list:
            raise Exception("Sensor Name List must be a list")
        if action_name_operation is None:
            raise Exception("no actions operation and action manager defined")
        if type(action_name_operation) is not dict:
            raise Exception("Action Name Operation must be a dict with key Action Name and the value the operation! ")

        command = []
        # ITERATE ALL OVER ACTION MANAGERS
        for action_operation_name, action_operation_obj in action_name_operation.items():
            # action_manager_name,action_obj = list(action_name_operation.items())[0]
            # action_obj = action_name_operation.values()
            command.append(self.__get_action_manager(action_operation_name).perform_action(action_operation_obj))

        command = ' '.join(command)

        sensor_list = []
        sensor_command_list = []
        sensor_buffer_list = []
        for sensor_name in sensor_name_list:
            sensor = self.__get_sensor(sensor_name)
            sensor_buffer_list.append(sensor.buffer_size)
            sensor_command_list.append(sensor.command)
            sensor_list.append(sensor)

        self.__sock.send_command('{} {}'.format(command, ' '.join(sensor_command_list)))
        data_hit = self.__sock.rec_byte()
        data_obs = self.__sock.rec_sensors_observations(sensor_buffer_list)
        hit = np.frombuffer(data_hit, dtype=np.uint8)
        obs_list = []

        for i in range(len(sensor_list)):
            obs_list.append(sensor_list[i].get_observation(data_obs[i]))

        return hit, obs_list

    def execute_raw_command(self, command_string):
        """
        Invia un comando grezzo (es. UnrealCV) direttamente tramite il socket ISAR
        senza attendere risposte complesse o processamento da parte degli Action Managers.
        """
        self.__sock.send_command(command_string)
        # Aggiungi una piccola pausa per assicurare che il motore elabori il comando.
        # Non aspettiamo una risposta, quindi non chiamiamo rec_byte o rec_sensors.
        time.sleep(2.0)

    # =================================================================
    # NUOVA FUNZIONE: RECUPERO COORDINATE PUNTO DI INTERESSE (PoI)
    # =================================================================

    def get_poi_coordinates(self):
        """
        Richiede le coordinate del Punto di Interesse (PoI) a Unreal Engine.
        Restituisce una tupla (x, y, z) in coordinate Unreal (centimetri).
        """
        self.__sock.send_command('POI')
        data = self.__sock.rec_bytes(1)[0].decode("utf-8").strip()

        # Formato atteso: "13 X Y Z" (dove 13 è il codice POI)
        parts = data.split()
        if len(parts) != 4:
            raise Exception(f"Formato risposta PoI non valido: {data}")

        poi_code = int(parts[0])
        x = float(parts[1])
        y = float(parts[2])
        z = float(parts[3])

        return (x, y, z)

    def close_connection(self):
        # self.__sock.send_command('CLOSE') # Rimosso/Commentato come da indicazioni
        self.__sock.close()
        for _, sensor in self.__sensor_set.items():
            if sensor is not None:
                sensor.close()