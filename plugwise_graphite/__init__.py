import plugwise
import anyconfig
from functools import partial
import time
import socket
from contextlib import closing
from itertools import cycle
import logging

log = logging.getLogger(__name__)

TEMPLATE = "{config[graphite][prefix]}{circle[name]} {circle[power_usage]} {time}\n"

def catch_error(call, *args, **kwargs):
    try:
        return call(*args, **kwargs)
    except (plugwise.exceptions.TimeoutException, ValueError):
        return None
    

def main():
    # config and logging
    config = anyconfig.load('config.yaml')
    logging.basicConfig(level=config.get('loglevel'))

    # setup plugwise stick
    stick = plugwise.Stick(config.get('tty'), config.get('timeout', 10))
    circle = partial(plugwise.Circle, comchan=stick)
    
    # configure circles
    circles = [dict(d, circle=circle(d.get('mac')), name=d.get('name', d.get('mac'))) for d in config.get('devices')]
    pool_queue = cycle(circles)

    # get active circles
    [c.__setitem__('active', bool(catch_error(c.get('circle').get_info))) for c in circles]
        
    while True:
        start = int(time.time())
        # get power usage for active devices
        [c.__setitem__('power_usage', catch_error(c.get('circle').get_power_usage)) for c in circles if c.get('active')]

        # remove inactive devices
        [c.__setitem__('active', False) for c in circles if c.get('power_usage') == None]

        # make autoclosing socket to graphite
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
            s.connect((config.get('graphite').get('host'), config.get('graphite').get('port')))

            # send metrics
            now = int(time.time())
            [log.info(TEMPLATE.format(config=config, circle=c, time=now).strip()) for c in circles if c.get('active')]
            [s.send(TEMPLATE.format(config=config, circle=c, time=now).encode('utf8')) for c in circles if c.get('active')]
        
        # want up to interval 
        while start + config.get('interval') > int(time.time()):
            # if there is enought time left, try to reconnect inactive circles
            if config.get('timeout') < start + config.get('interval') - int(time.time()):
                try_circle = next(pool_queue)
                log.debug('trying {c[name]}'.format(c=try_circle))
                try_circle['active'] = bool(catch_error(try_circle.get('circle').get_info))
            time.sleep(1)

if __name__ == "__main__":
    main()
