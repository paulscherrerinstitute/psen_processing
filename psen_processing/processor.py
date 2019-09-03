import datetime
from collections import deque
from logging import getLogger

import numpy as np
from zmq import Again

from bsread import PULL, json, source
from bsread.sender import sender
from psen_processing import config
from psen_processing.utils import append_message_data

_logger = getLogger(__name__)

background = deque(maxlen=4)


def get_roi_x_profile(image, roi):
    offset_x, size_x, offset_y, size_y = roi
    roi_image = image[offset_y:offset_y + size_y, offset_x:offset_x + size_x]

    return roi_image.sum(0)


def find_edge(data, step_length=50, edge_type='falling', refinement=1):
    # refine data
    def _interp(fp, xp, x):  # utility function to be used with apply_along_axis
        return np.interp(x, xp, fp)

    data_length = data.shape[1]
    refined_data = np.apply_along_axis(
        _interp,
        axis=1,
        arr=data,
        x=np.arange(0, data_length - 1, refinement),
        xp=np.arange(data_length),
    )

    # prepare a step function and refine it
    step_waveform = np.ones(shape=(step_length,))
    if edge_type == 'rising':
        step_waveform[: int(step_length / 2)] = -1
    elif edge_type == 'falling':
        step_waveform[int(step_length / 2) :] = -1

    step_waveform = np.interp(
        x=np.arange(0, step_length - 1, refinement),
        xp=np.arange(step_length),
        fp=step_waveform,
    )

    # find edges
    xcorr = np.apply_along_axis(np.correlate, 1, refined_data, v=step_waveform, mode='valid')
    edge_position = np.argmax(xcorr, axis=1).astype(float) * refinement
    xcorr_amplitude = np.amax(xcorr, axis=1)

    # correct edge_position for step_length
    edge_position += np.floor(step_length / 2)

    return {'edge_pos': edge_position, 'xcorr_ampl': xcorr_amplitude}


def process_image(pulse_id, image, image_property_name, roi_signal, roi_background):
    processed_data = dict()

    processed_data[image_property_name + ".processing_parameters"] = json.dumps({"roi_signal": roi_signal,
                                                                                 "roi_background": roi_background})

    if roi_signal:
        signal_profile = get_roi_x_profile(image, roi_signal)
        processed_data[image_property_name + ".roi_signal_x_profile"] = signal_profile

        if pulse_id%4 == 0:
            # fel shot
            if background:
                avg_background = sum(background) / len(background)
                output = find_edge(signal_profile - avg_background)
            else:
                output['edge_pos'] = np.nan
                output['xcorr_ampl'] = np.nan
        else:
            background.append(signal_profile)
            output['edge_pos'] = np.nan
            output['xcorr_ampl'] = np.nan

        processed_data[image_property_name + ".edge_position"] = output['edge_pos']
        processed_data[image_property_name + ".cross_correlation_amplitude"] = output['xcorr_ampl']

    if roi_background:
        processed_data[image_property_name + ".roi_background_x_profile"] = get_roi_x_profile(image, roi_background)

    return processed_data


def get_stream_processor(input_stream_host, input_stream_port, data_output_stream_port,
                         image_output_stream_port, epics_pv_name_prefix):
    def stream_processor(running_flag, roi_signal, roi_background, statistics):
        try:
            running_flag.set()

            _logger.info("Connecting to input_stream_host %s and input_stream_port %s.",
                         input_stream_host, input_stream_port)

            _logger.info("Sending out data on stream port %s.", data_output_stream_port)

            with source(host=input_stream_host, port=input_stream_port, mode=PULL,
                        queue_size=config.INPUT_STREAM_QUEUE_SIZE,
                        receive_timeout=config.INPUT_STREAM_RECEIVE_TIMEOUT) as input_stream:

                with sender(port=data_output_stream_port,
                            send_timeout=config.DATA_OUTPUT_STREAM_SEND_TIMEOUT) as data_output_stream:

                    with sender(port=image_output_stream_port, block=False,
                                queue_size=config.IMAGE_OUTPUT_STREAM_QUEUE_SIZE) as image_output_stream:

                        statistics["processing_start_time"] = str(datetime.datetime.now())
                        statistics["last_sent_pulse_id"] = None
                        statistics["last_sent_time"] = None
                        statistics["n_processed_images"] = 0

                        image_property_name = epics_pv_name_prefix + config.EPICS_PV_SUFFIX_IMAGE

                        _logger.info("Using image property name '%s'.", image_property_name)

                        while running_flag.is_set():

                            message = input_stream.receive()

                            if message is None:
                                continue

                            pulse_id = message.data.pulse_id
                            timestamp = (message.data.global_timestamp, message.data.global_timestamp_offset)

                            _logger.debug("Received message with pulse_id %s", pulse_id)

                            image = message.data.data[image_property_name].value
                            processed_data = process_image(pulse_id, image, image_property_name, roi_signal, roi_background)

                            # Send out processed data.
                            try:
                                data_output_stream.send(pulse_id=pulse_id,
                                                        timestamp=timestamp,
                                                        data=processed_data)

                                _logger.debug("Sent data message with pulse_id %s", pulse_id)

                                statistics["last_sent_pulse_id"] = pulse_id
                                statistics["last_sent_time"] = str(datetime.datetime.now())
                                statistics["n_processed_images"] = statistics.get("n_processed_images", 0) + 1

                            except Again:
                                pass

                            # Send out image.
                            try:
                                image_output_stream.send(pulse_id=pulse_id,
                                                         timestamp=timestamp,
                                                         data={image_property_name: image})

                                _logger.debug("Sent image message with pulse_id %s", pulse_id)

                            except Again:
                                pass

        except Exception as e:
            _logger.error("Error while processing the stream. Exiting. Error: ", e)
            running_flag.clear()

            raise

        except KeyboardInterrupt:
            _logger.warning("Terminating processing due to user request.")
            running_flag.clear()

            raise

    return stream_processor
