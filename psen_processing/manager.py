class ProcessingManager(object):

    def __init__(self, stream_processor, auto_start=False):
        self.processor = stream_processor
        self.auto_start = auto_start

    def start(self):
        pass

    def stop(self):
        pass

    def set_roi(self, roi_index, roi_config):
        pass

    def get_roi(self, roi_index=None):
        pass

    def get_statistics(self):
        pass

    def get_status(self):
        pass