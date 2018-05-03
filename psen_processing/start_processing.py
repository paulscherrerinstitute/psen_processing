import argparse
import logging

from psen_processing import config

_logger = logging.getLogger(__name__)


def start_processing(input_stream, output_stream_port, rest_api_port, bs_data_prefix):
    pass


def main():
    parser = argparse.ArgumentParser(description='PSEN camera processing.')
    parser.add_argument('-i', '--input_stream', help="Input bsread stream to process.")
    parser.add_argument('-o', '--output_stream_port', default=config.DEFAULT_OUTPUT_STREAM_PORT,
                        help="Output bsread stream port.")
    parser.add_argument('-r', '--rest_api_port', default=config.DEFAULT_REST_API_PORT, help="REST Api port.")
    parser.add_argument('-p', '--prefix', default=None, help="Prefix to append to bsread value names in output stream.")
    parser.add_argument("--log_level", default=config.DEFAULT_LOGGING_LEVEL,
                        choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG'],
                        help="Log level to use.")
    arguments = parser.parse_args()

    # Setup the logging level.
    logging.basicConfig(level=arguments.log_level)

    start_processing(input_stream=arguments.input_stream,
                     output_stream_port=arguments.output_stream_port,
                     rest_api_port=arguments.rest_api_port,
                     bs_data_prefix=arguments.prefix)


if __name__ == "__main__":
    main()
