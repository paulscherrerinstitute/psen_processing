from logging import getLogger

_logger = getLogger(__name__)


def get_stream_processor(input_stream, output_stream_port, bs_data_prefix):

    def stream_processor(running_flag, roi_signal, roi_background):
        try:
            # TODO: Connect to the stream, open output stream.

            running_flag.set()

            while running_flag.is_set():
                pass

        except Exception as e:
            _logger.error("Error while processing the stream. Exiting. Error: ", e)
            running_flag.clear()

    return stream_processor
