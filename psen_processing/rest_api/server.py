import json
import logging

import bottle
from bottle import request, response

from psen_processing import config

_logger = logging.getLogger(__name__)


def register_rest_interface(app, instance_manager):

    api_root_address = config.API_PREFIX

    @app.get(api_root_address + "/roi")
    @app.get(api_root_address + "/roi/<int:roi_index>")
    def get_roi(roi_index=None):

        return {"state": "ok",
                "status": "Current ROI configuration.s",
                "cameras": instance_manager.get_roi(roi_index)}

    @app.post(api_root_address + "/roi/<int:roi_index>")
    def set_roi(roi_index):

        roi_config = request.json

        return {"state": "ok",
                "status": "ROI index %d is set." % roi_index,
                "stream": instance_manager.set_roi(roi_index, roi_config)}

    @app.get(api_root_address + "/statistics")
    def get_statistics():

        return {"state": "ok",
                "status": "Instance statistics.",
                "statistics": instance_manager.get_statistics()}

    @app.error(405)
    def method_not_allowed(res):
        if request.method == 'OPTIONS':
            new_res = bottle.HTTPResponse()
            new_res.set_header('Access-Control-Allow-Origin', '*')
            new_res.set_header('Access-Control-Allow-Methods', 'PUT, GET, POST, DELETE, OPTIONS')
            new_res.set_header('Access-Control-Allow-Headers', 'Origin, Accept, Content-Type')
            return new_res
        res.headers['Allow'] += ', OPTIONS'
        return request.app.default_error_handler(res)

    @app.hook('after_request')
    def enable_cors():
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'PUT, GET, POST, DELETE, OPTIONS'
        response.headers[
            'Access-Control-Allow-Headers'] = 'Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token'

    @app.error(500)
    def error_handler_500(error):
        response.content_type = 'application/json'
        response.status = 200

        return json.dumps({"state": "error",
                           "status": str(error.exception)})
