import unittest
from time import sleep

import numpy
from bsread.sender import sender
from multiprocessing import Process, Event
from bsread import source, PULL, json

from psen_processing import config
from psen_processing.processor import get_roi_x_profile, process_image, get_stream_processor


class TestProcessing(unittest.TestCase):
    def test_get_roi_x_profile(self):
        image = numpy.zeros(shape=(1024, 1024), dtype="uint16")
        image += 1

        roi = [0, 1024, 0, 1024]
        x_profile = get_roi_x_profile(image, roi)

        self.assertEqual(len(x_profile), 1024)
        self.assertListEqual(list(x_profile), [1024] * 1024)

        roi = [0, 100, 0, 1024]
        x_profile = get_roi_x_profile(image, roi)

        self.assertEqual(len(x_profile), 100)
        self.assertListEqual(list(x_profile), [1024] * 100)

        roi = [0, 100, 0, 100]
        x_profile = get_roi_x_profile(image, roi)

        self.assertEqual(len(x_profile), 100)
        self.assertListEqual(list(x_profile), [100] * 100)

    def test_process_image(self):
        image = numpy.zeros(shape=(1024, 1024), dtype="uint16")
        image += 1

        image_property_name = "TESTING_IMAGE"

        roi_signal = [0, 1024, 0, 1024]
        roi_background = []

        processed_data = process_image(image, image_property_name, roi_signal, roi_background)

        self.assertSetEqual(set(processed_data.keys()), {image_property_name + ".processing_parameters",
                                                         image_property_name + ".roi_signal_x_profile"})

        roi_signal = [0, 1024, 0, 1024]
        roi_background = [0, 100, 0, 100]

        processed_data = process_image(image, image_property_name, roi_signal, roi_background)

        self.assertSetEqual(set(processed_data.keys()), {image_property_name + ".processing_parameters",
                                                         image_property_name + ".roi_signal_x_profile",
                                                         image_property_name + ".roi_background_x_profile"})

        self.assertEqual(len(processed_data[image_property_name + ".roi_signal_x_profile"]), 1024)
        self.assertListEqual(list(processed_data[image_property_name + ".roi_signal_x_profile"]), [1024] * 1024)

        self.assertEqual(len(processed_data[image_property_name + ".roi_background_x_profile"]), 100)
        self.assertListEqual(list(processed_data[image_property_name + ".roi_background_x_profile"]), [100] * 100)

    def test_stream_processor(self):
        pv_name_prefix = "JUST_TESTING"
        n_images = 5
        original_roi_signal = [0, 1024, 0, 1024]
        original_roi_background = [0, 100, 0, 100]

        image = numpy.zeros(shape=(1024, 1024), dtype="uint16")
        image += 1

        data_to_send = {pv_name_prefix + config.EPICS_PV_SUFFIX_IMAGE: image}

        def send_data():
            sleep(1)
            with sender(port=10000) as output_stream:
                for x in range(n_images):
                    output_stream.send(data=data_to_send)

        def process_data(event):
            stream_processor = get_stream_processor(input_stream_host="localhost",
                                                    input_stream_port=10000,
                                                    data_output_stream_port=11000,
                                                    image_output_stream_port=11001,
                                                    epics_pv_name_prefix=pv_name_prefix)

            stream_processor(event, original_roi_signal, original_roi_background, {})

        running_event = Event()

        send_process = Process(target=send_data)
        processing_process = Process(target=process_data, args=(running_event,))

        send_process.start()
        processing_process.start()

        data_received = []

        with source(host="localhost", port=11000, mode=PULL, receive_timeout=2000) as input_stream:
            for _ in range(n_images):
                data_received.append(input_stream.receive())

        running_event.clear()

        sleep(0.2)

        send_process.terminate()
        processing_process.terminate()

        self.assertEqual(len(data_received), n_images)

        parameters = data_received[0].data.data[pv_name_prefix + config.EPICS_PV_SUFFIX_IMAGE +
                                                ".processing_parameters"].value
        processing_parameters = json.loads(parameters)

        self.assertEqual(processing_parameters["roi_signal"], original_roi_signal)
        self.assertEqual(processing_parameters["roi_background"], original_roi_background)

        roi_signal = data_received[0].data.data[pv_name_prefix + config.EPICS_PV_SUFFIX_IMAGE +
                                                ".roi_signal_x_profile"].value

        self.assertEqual(len(roi_signal), 1024)
        self.assertListEqual(list(roi_signal), [1024] * 1024)

        roi_background = data_received[0].data.data[pv_name_prefix + config.EPICS_PV_SUFFIX_IMAGE +
                                                    ".roi_background_x_profile"].value

        self.assertEqual(len(roi_background), 100)
        self.assertListEqual(list(roi_background), [100] * 100)
