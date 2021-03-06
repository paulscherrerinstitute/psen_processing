import json
import logging

import bottle
from bottle import request, response

from psen_processing import config

_logger = logging.getLogger(__name__)


def register_rest_interface(app, instance_manager):

    api_root_address = config.API_PREFIX

    @app.post(api_root_address + "/start")
    def start():

        instance_manager.start()

        return {"state": "ok",
                "status": instance_manager.get_status()}

    @app.post(api_root_address + "/stop")
    def stop():

        instance_manager.stop()

        return {"state": "ok",
                "status": instance_manager.get_status()}

    @app.get(api_root_address + "/status")
    def get_status():
        return {"state": "ok",
                "status": instance_manager.get_status()}

    @app.get(api_root_address + "/roi_background")
    def get_roi_background():

        return {"state": "ok",
                "status": instance_manager.get_status(),
                "roi_background": instance_manager.get_roi_background()}

    @app.post(api_root_address + "/roi_background")
    def set_roi_background():

        roi_background = request.json
        instance_manager.set_roi_background(roi_background)

        return {"state": "ok",
                "status": instance_manager.get_status(),
                "roi_background": instance_manager.get_roi_background()}

    @app.get(api_root_address + "/roi_signal")
    def get_roi_signal():
        return {"state": "ok",
                "status": instance_manager.get_status(),
                "roi_signal": instance_manager.get_roi_signal()}

    @app.post(api_root_address + "/roi_signal")
    def set_roi_signal():

        roi_signal = request.json
        instance_manager.set_roi_signal(roi_signal)

        return {"state": "ok",
                "status": instance_manager.get_status(),
                "roi_signal": instance_manager.get_roi_signal()}

    @app.get(api_root_address + "/statistics")
    def get_statistics():

        return {"state": "ok",
                "status": instance_manager.get_status(),
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
        response.headers['Access-Control-Allow-Headers'] = \
            'Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token'

    @app.error(500)
    def error_handler_500(error):

        response.content_type = 'application/json'
        response.status = 200

        return json.dumps({"state": "error",
                           "status": str(error.exception)})
