import argparse
import logging

import bottle

from psen_processing import config
from psen_processing.manager import ProcessingManager
from psen_processing.processor import get_stream_processor
from psen_processing.rest_api.server import register_rest_interface
from psen_processing.utils import get_host_port_from_stream_address

_logger = logging.getLogger(__name__)


def start_processing(input_stream, data_output_stream_port, image_output_stream_port, rest_api_interface, rest_api_port,
                     epics_pv_name_prefix, auto_start):

    _logger.info("Receiving data from %s and outputting data on port %s and images on port %s.",
                 input_stream, data_output_stream_port, image_output_stream_port)
    _logger.info("Looking for image with Epics PV name prefix '%s'.", epics_pv_name_prefix)

    input_stream_host, input_stream_port = get_host_port_from_stream_address(input_stream)

    stream_processor = get_stream_processor(input_stream_host=input_stream_host,
                                            input_stream_port=input_stream_port,
                                            data_output_stream_port=data_output_stream_port,
                                            image_output_stream_port=image_output_stream_port,
                                            epics_pv_name_prefix=epics_pv_name_prefix)

    _logger.info("Auto start set to %s.", auto_start)
    manager = ProcessingManager(stream_processor=stream_processor,
                                auto_start=auto_start)

    app = bottle.Bottle()

    register_rest_interface(app, manager)

    try:
        _logger.info("Starting REST interface on interface %s and port %s.", rest_api_interface, rest_api_port)
        bottle.run(app=app, host=rest_api_interface, port=rest_api_port, debug=True)
    finally:
        pass


def main():
    parser = argparse.ArgumentParser(description='PSEN camera processing.')
    parser.add_argument('input_stream', help="Input bsread stream to process.")
    parser.add_argument('prefix', help="Epics PV prefix of the image.")

    parser.add_argument('-o', '--data_output_stream_port', type=int, default=config.DEFAULT_DATA_OUTPUT_STREAM_PORT,
                        help="Output data bsread stream port.")
    parser.add_argument('-i', '--image_output_stream_port', type=int, default=config.DEFAULT_IMAGE_OUTPUT_STREAM_PORT,
                        help="Output image bsread stream port.")

    parser.add_argument('-r', '--rest_api_port', default=config.DEFAULT_REST_API_PORT, help="REST Api port.")
    parser.add_argument('--rest_api_interface', default=config.DEFAULT_REST_API_INTERFACE,
                        help="Hostname interface to bind to")

    parser.add_argument("--log_level", default=config.DEFAULT_LOGGING_LEVEL,
                        choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG'],
                        help="Log level to use.")
    parser.add_argument("--auto_start", action="store_true", help="Start the processing as soon as "
                                                                  "the service is started.")
    arguments = parser.parse_args()

    logging.basicConfig(level=arguments.log_level)

    _logger.info("Using log level %s.", arguments.log_level)

    start_processing(input_stream=arguments.input_stream,
                     data_output_stream_port=arguments.data_output_stream_port,
                     image_output_stream_port=arguments.image_output_stream_port,
                     rest_api_interface=arguments.rest_api_interface,
                     rest_api_port=arguments.rest_api_port,
                     epics_pv_name_prefix=arguments.prefix,
                     auto_start=arguments.auto_start)


if __name__ == "__main__":
    main()
