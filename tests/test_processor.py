import unittest

import numpy

from psen_processing.processor import get_roi_x_profile, process_image


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

        self.assertSetEqual(set(processed_data.keys()), {image_property_name + "_processing_parameters",
                                                         image_property_name + "_roi_signal_x_profile"})

        roi_signal = [0, 1024, 0, 1024]
        roi_background = [0, 100, 0, 100]

        processed_data = process_image(image, image_property_name, roi_signal, roi_background)

        self.assertSetEqual(set(processed_data.keys()), {image_property_name + "_processing_parameters",
                                                         image_property_name + "_roi_signal_x_profile",
                                                         image_property_name + "_roi_background_x_profile"})

        self.assertEqual(len(processed_data[image_property_name + "_roi_signal_x_profile"]), 1024)
        self.assertListEqual(list(processed_data[image_property_name + "_roi_signal_x_profile"]), [1024] * 1024)

        self.assertEqual(len(processed_data[image_property_name + "_roi_background_x_profile"]), 100)
        self.assertListEqual(list(processed_data[image_property_name + "_roi_background_x_profile"]), [100] * 100)

    def test_stream_processor(self):
        # TODO: Implement.
        pass
