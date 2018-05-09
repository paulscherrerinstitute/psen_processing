import datetime
from logging import getLogger

from bsread import source
from bsread.sender import sender

from psen_processing import config

_logger = getLogger(__name__)


def process_message(message, roi_signal, roi_background, bs_data_prefix=""):
    return {}


def get_stream_processor(input_stream_host, input_stream_port, output_stream_port, bs_data_prefix):

    def stream_processor(running_flag, roi_signal, roi_background, statistics):
        try:
            running_flag.set()

            with source(host=input_stream_host, port=input_stream_port,
                        queue_size=config.INPUT_STREAM_QUEUE_SIZE) as input_stream:

                with sender(port=output_stream_port) as output_stream:

                    statistics["processing_start_time"] = datetime.datetime.now()

                    while running_flag.is_set():

                        message = input_stream.receive()

                        if message is None:
                            continue

                        pulse_id = message.data.pulse_id
                        timestamp = (message.data.global_timestamp, message.data.global_timestamp_offset)

                        _logger.debug("Received message with pulse_id %s", pulse_id)

                        data = process_message(message, roi_signal, roi_background, bs_data_prefix)

                        output_stream.send(pulse_id=pulse_id,
                                           timestamp=timestamp,
                                           data=data)

                        _logger.debug("Sent message with pulse_id %s", pulse_id)

                        statistics["last_sent_pulse_id"] = pulse_id
                        statistics["last_sent_time"] = datetime.datetime.now()

        except Exception as e:
            _logger.error("Error while processing the stream. Exiting. Error: ", e)
            running_flag.clear()

        except KeyboardInterrupt:
            _logger.warning("Terminating processing due to user request.")
            running_flag.clear()

    return stream_processor
