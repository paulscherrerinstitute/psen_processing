def validate_roi(roi):
    """
    Check if the ROI parameters are valid.
    :param roi: [offset_x, size_x, offset_y, size_y]
    :raises ValueError: When ROI is not valid, it raises a ValueError.
    """

    if not isinstance(roi, list):
        raise ValueError("ROI must be an instance of a list, but %s was given as a %s." % (roi, type(roi)))

    if len(roi) == 0:
        return

    if len(roi) != 4:
        raise ValueError("ROI must have exactly 4 elements, but %s was given." % roi)

    if roi[0] < 0 or roi[2] < 0:
        raise ValueError("ROI offsets (first and third elements) must be positive, but %s was given." % roi)

    if roi[1] < 1 or roi[3] < 1:
        raise ValueError("ROI sizes (second and fourth elements) must be at least 1, but %s was given." % roi)


def get_host_port_from_stream_address(stream_address):
    source_host, source_port = stream_address.rsplit(":", maxsplit=1)
    source_host = source_host.split("//")[1]

    return source_host, int(source_port)
