from syndatatoolbox_api import environment
import time
import warnings
warnings.simplefilter("always")

if __name__ == "__main__":
    setup = {
        'show': True,
        'image_folder_path': None,
        'mask_folder_path': None,
        'mask_colorized': 'GRAYSCALE',  # RGB or GRAYSCALE
        'format_output_mask': '.png',
        'segmentation_video_path': None,
        'bounding_box_file_path': None,
        'bounding_box_print_output': True,
        'video_path': None,
        'render': True
    }

    environment = environment.Environment(port=9734, address='localhost', setup=setup)

    # rate = 30  # Hz
    while True:
        start = time.time()
        v = 0  # 10
        w = 0  # 0.5
        dt = 0.01  # 1/rate

        environment.perform_action('AckermannActionManager(AckermannActionManagerSDT)',
                                   {'UPDATESETPOINTS': [v, w, dt]})
        # pos = environment.get_obs(['GPS(GPSSDT)'])
        pc = environment.get_obs(['Lidar(LidarSDT)'])
        # print(pc)
        # print('\n')

        # elapsed_time = time.time() - start
        # try:
        #     time.sleep(1/rate - elapsed_time)
        # except ValueError:
        #     message = "Requested rate (%i Hz) is too high (elapsed time: %f)" % (rate, elapsed_time)
        #     warnings.warn(message)

        # environment.env_step(['AckermannActionManager(AckermannActionManagerSDT)', {'UPDATESETPOINTS': [10, 0]}],
        #                      ['RGBCamera(CameraSDT)'])
        # img = environment.get_obs(['RGBCamera(CameraSDT)'])

    # sensor_settings = {
    #         'RGBCamera(CameraSDT)': {
    #         'Width':512,
    #         'Height':512,
    #         'FOV':90
    #     },
    #     'SegmentationCamera(SegmentationCameraSDT)' : {
    #         'Width':512,
    #         'Height':512,
    #         'FOV':90,
    #         'Classes':{
    #             'Chair':1,
    #             'Pyramid':2,
    #             'Floor':10
    #         }
    #     },
    #     }
    # }
    # environment.change_sensor_settings(sensor_settings=sensor_settings)

    environment.close_connection()
