from __future__ import print_function
import plugwise
import anyconfig
from functools import partial
import time
import socket
from contextlib import closing
from itertools import cycle
import logging
from . import catch_error

log = logging.getLogger(__name__)

C_TEMPLATE = "{config[graphite][prefix]}{circle[name]} {circle[power_usage]} {time}"
TEMPLATE = "{config[graphite][prefix]}{name} {value} {time}"


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
    log.info('probing %s devices', len(circles))
    [c.__setitem__('active', bool(catch_error(c.get('circle').get_info) != -1)) for c in circles]

    while True:
        start = int(time.time())
        # get power usage for active devices
        [c.__setitem__('power_usage', catch_error(c.get('circle').get_power_usage)) for c in circles if c.get('active')]

        # remove inactive devices
        [c.__setitem__('active', False) for c in circles if c.get('power_usage') == None]

        now = int(time.time())
        msg = "\n".join([C_TEMPLATE.format(config=config, circle=c, time=now)
            for c in circles if c.get('active')]) + '\n'
        read_devices = len([c for c in circles if c.get('active')])
        msg += TEMPLATE.format(config=config, name='read_devices', value=read_devices, time=now)
        log.info(msg)

        if config.get('stdout'):
            print(msg + '\n')
        else:
            # make autoclosing socket to graphite
            with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
                s.connect((config.get('graphite').get('host'), config.get('graphite').get('port')))
                s.send(msg + '\n')

        # want up to interval
        while start + config.get('interval') > int(time.time()):
            # if there is enought time left, try to reconnect inactive circles
            if config.get('timeout') < start + config.get('interval') - int(time.time()):
                try_circle = next(pool_queue)
                log.debug('trying {c[name]}'.format(c=try_circle))
                try_circle['active'] = bool(catch_error(try_circle.get('circle').get_info) != -1)
            time.sleep(1)

if __name__ == "__main__":
    main()
