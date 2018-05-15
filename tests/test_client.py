import unittest
from time import sleep

import numpy
from bsread.sender import sender
from bsread import source, PULL, json
from multiprocessing import Process

from psen_processing import config, PsenProcessingClient
from psen_processing.start_processing import start_processing


class TestClient(unittest.TestCase):

    def setUp(self):
        self.n_images = 5
        self.pv_name_prefix = "JUST_TESTING"

        self.image = numpy.zeros(shape=(1024, 1024), dtype="uint16")
        self.image += 1

        data_to_send = {self.pv_name_prefix + config.EPICS_PV_SUFFIX_IMAGE: self.image}

        def send_data():
            with sender(port=11000) as output_stream:
                for x in range(self.n_images):
                    output_stream.send(data=data_to_send)

        def process_data():
            start_processing(input_stream="tcp://localhost:11000",
                             output_stream_port=12000,
                             rest_api_interface="0.0.0.0",
                             rest_api_port=10000,
                             epics_pv_name_prefix=self.pv_name_prefix,
                             auto_start=False)

        self.sending_process = Process(target=send_data)
        self.processing_process = Process(target=process_data)

        self.sending_process.start()
        self.processing_process.start()

        sleep(1)

    def tearDown(self):
        if self.sending_process:
            self.sending_process.terminate()

        if self.processing_process:
            self.processing_process.terminate()

        sleep(1)

    def test_classic_interaction(self):
        client = PsenProcessingClient("http://localhost:10000/")

        self.assertEqual(client.get_status(), "stopped")

        self.assertListEqual(client.get_roi_signal(), [])
        self.assertListEqual(client.get_roi_background(), [])

        client.set_roi_signal(None)
        self.assertListEqual(client.get_roi_signal(), [])

        with self.assertRaisesRegex(ValueError, "ROI offsets"):
            client.set_roi_signal([-1, -1, -1, -1])

        roi_signal = [0, 1024, 0, 1024]
        client.set_roi_signal(roi_signal)
        self.assertListEqual(client.get_roi_signal(), roi_signal)

        roi_background = [0, 100, 0, 100]
        client.set_roi_background(roi_background)
        self.assertListEqual(client.get_roi_background(), roi_background)

        self.assertDictEqual(client.get_statistics(), {})

        client.start()
        self.assertEqual(client.get_status(), "processing")

        statistics = client.get_statistics()
        self.assertEqual(len(statistics), 4)
        self.assertTrue("processing_start_time" in statistics)
        self.assertTrue("last_sent_pulse_id" in statistics)
        self.assertTrue("last_sent_time" in statistics)
        self.assertTrue("n_processed_images" in statistics)

        processed_data = []

        with source(host="localhost", port=12000, mode=PULL, receive_timeout=1000) as input_stream:
            for index in range(self.n_images):
                processed_data.append(input_stream.receive())

        statistics = client.get_statistics()
        self.assertEqual(client.get_statistics()["n_processed_images"], self.n_images)

        # Pulse ids are 0 based.
        self.assertEqual(client.get_statistics()["last_sent_pulse_id"], self.n_images - 1)

        self.assertTrue("processing_start_time" in statistics)
        self.assertTrue("last_sent_time" in statistics)

        self.assertEqual(client.get_status(), "processing")

        client.stop()
        self.assertEqual(client.get_status(), "stopped")

        client.start()
        self.assertEqual(client.get_status(), "processing")

        client.stop()
        self.assertEqual(client.get_status(), "stopped")

    def test_change_roi_while_running(self):
        client = PsenProcessingClient("http://localhost:10000/")

        roi_signal = [0, 1024, 0, 1024]
        client.set_roi_signal(roi_signal)

        roi_background = [0, 100, 0, 100]
        client.set_roi_background(roi_background)

        client.start()

        processed_data = []

        with source(host="localhost", port=12000, mode=PULL, receive_timeout=1000) as input_stream:
            for index in range(self.n_images):
                processed_data.append(input_stream.receive())

        updated_roi_signal = [100, 200, 100, 200]
        client.set_roi_signal(updated_roi_signal)

        data_to_send = {self.pv_name_prefix + config.EPICS_PV_SUFFIX_IMAGE: self.image}

        with sender(port=11000) as output_stream:
            for x in range(self.n_images):
                output_stream.send(data=data_to_send)

        with source(host="localhost", port=12000, mode=PULL, receive_timeout=1000) as input_stream:
            for index in range(self.n_images):
                processed_data.append(input_stream.receive())

        client.stop()

        processing_parameters_name = self.pv_name_prefix + config.EPICS_PV_SUFFIX_IMAGE + ".processing_parameters"

        start_processing_parameters = json.loads(processed_data[0].data.data[processing_parameters_name].value)
        end_processing_parameters = json.loads(processed_data[9].data.data[processing_parameters_name].value)

        self.assertListEqual(roi_signal, start_processing_parameters["roi_signal"])
        self.assertListEqual(updated_roi_signal, end_processing_parameters["roi_signal"])

    def test_no_roi(self):
        client = PsenProcessingClient("http://localhost:10000/")

        roi_signal = []
        client.set_roi_signal(roi_signal)

        roi_background = None
        client.set_roi_background(roi_background)

        client.start()

        processed_data = []

        with source(host="localhost", port=12000, mode=PULL, receive_timeout=1000) as input_stream:
            for index in range(self.n_images):
                processed_data.append(input_stream.receive())

        client.stop()

        roi_signal_parameter_name = self.pv_name_prefix + config.EPICS_PV_SUFFIX_IMAGE + ".roi_signal_x_profile"
        roi_background_parameter_name = self.pv_name_prefix + config.EPICS_PV_SUFFIX_IMAGE + ".roi_background_x_profile"

        # All the messages should be equal.
        received_data = processed_data[0]

        # If the roi is not set, the value should not be added to the output.
        self.assertTrue(roi_signal_parameter_name not in received_data.data.data)
        self.assertTrue(roi_background_parameter_name not in received_data.data.data)

    def test_stop_when_blocking_send(self):
        client = PsenProcessingClient("http://localhost:10000/")

        client.start()

        def stop_client():
            client = PsenProcessingClient("http://localhost:10000/")
            client.stop()

        stop_process = Process(target=stop_client)
        stop_process.start()

        sleep(0.5)

        if stop_process.is_alive() and not stop_process.join(timeout=3):
            stop_process.terminate()
            raise ValueError("The stop call is blocked.")

    def test_received_data_on_send_timeout(self):
        client = PsenProcessingClient("http://localhost:10000/")
        client.start()

        processed_data = []

        with source(host="localhost", port=12000, mode=PULL, receive_timeout=1000) as input_stream:
            for index in range(self.n_images):

                if index == 2:
                    # Wait for the send timeout to happen.
                    sleep(config.OUTPUT_STREAM_SEND_TIMEOUT + 1)

                processed_data.append(input_stream.receive())

        for index, data in enumerate(processed_data):
            self.assertEqual(data.data.pulse_id, index)