import argparse
import logging

from psen_processing import config
from psen_processing.manager import ProcessingManager
from psen_processing.processor import get_stream_processor
from psen_processing.rest_api.server import register_rest_interface

_logger = logging.getLogger(__name__)


def start_processing(input_stream, output_stream_port, rest_api_interface, rest_api_port, bs_data_prefix, auto_start):
    _logger.info("Receiving data from %s. and outputting results on port %s with bsread data prefix %s.",
                 input_stream, output_stream_port, bs_data_prefix)

    stream_processor = get_stream_processor(input_stream=input_stream,
                                            output_stream_port=output_stream_port,
                                            bs_data_prefix=bs_data_prefix)

    _logger.info("Auto start set to %s.", auto_start)
    manager = ProcessingManager(stream_processor, auto_start)

    app = bottle.Bottle()

    register_rest_interface(app, manager)

    try:
        _logger.info("Starting REST interface on interface %s and port %s.", rest_api_interface, rest_api_port)
        bottle.run(app=app, host=rest_api_interface, port=rest_api_port, debug=True)
    finally:
        pass


def main():
    parser = argparse.ArgumentParser(description='PSEN camera processing.')
    parser.add_argument('-i', '--input_stream', help="Input bsread stream to process.")
    parser.add_argument('-o', '--output_stream_port', default=config.DEFAULT_OUTPUT_STREAM_PORT,
                        help="Output bsread stream port.")
    parser.add_argument('-r', '--rest_api_port', default=config.DEFAULT_REST_API_PORT, help="REST Api port.")
    parser.add_argument('--rest_api_interface', default=config.DEFAULT_REST_API_INTERFACE,
                        help="Hostname interface to bind to")
    parser.add_argument('-p', '--prefix', default=None, help="Prefix to append to bsread value names in output stream.")
    parser.add_argument("--log_level", default=config.DEFAULT_LOGGING_LEVEL,
                        choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG'],
                        help="Log level to use.")
    parser.add_argument("--auto_start", action="store_true", help="Start the processing as soon as "
                                                                  "the service is started.")
    arguments = parser.parse_args()

    logging.basicConfig(level=arguments.log_level)

    _logger.info("Using log level %s.", arguments.log_level)

    start_processing(input_stream=arguments.input_stream,
                     output_stream_port=arguments.output_stream_port,
                     rest_api_interface=arguments.rest_api_interface,
                     rest_api_port=arguments.rest_api_port,
                     bs_data_prefix=arguments.prefix,
                     auto_start=arguments.auto_start)


if __name__ == "__main__":
    main()
