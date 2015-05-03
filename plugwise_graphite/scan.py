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

def main():
    # config and logging
    config = anyconfig.load('config.yaml')
    logging.basicConfig(level=config.get('loglevel'))

    # setup plugwise stick
    stick = plugwise.Stick(config.get('tty'), config.get('timeout', 10))
    circle = partial(plugwise.Circle, comchan=stick)

    # configure circles
    circles = [dict(d, circle=circle(d.get('mac')), name=d.get('name', d.get('mac'))) for d in config.get('devices')]
    log.info('probing %s devices', len(circles))

    while True:
        # get power usage for active devices
        [log.info('{:20s}: {:6.2f}W'.format(c.get('name'), catch_error(c.get('circle').get_power_usage)))
            for c in circles]

if __name__ == "__main__":
    main()
