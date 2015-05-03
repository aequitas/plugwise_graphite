import plugwise

def catch_error(call, *args, **kwargs):
    try:
        return call(*args, **kwargs)
    except (plugwise.exceptions.TimeoutException, ValueError):
        return -1

