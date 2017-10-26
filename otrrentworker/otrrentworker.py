""" imports & globals """
import logging
import logging.handlers
import signal
import schedule
import time

""" import config and workers """
from config import (
    config, 
    log
    )

from etl import runetl
from worker import runworker

""" schedule workers """
schedule.every(5).minutes.do(runworker, config, log)
schedule.every().day.at("00:30").do(runetl, config, log)


""" handle sigterm and sigint """
stopsignal = False
def handler_stop_signals(signum, frame):
    global stopsignal
    stopsignal = True
signal.signal(signal.SIGINT, handler_stop_signals)
signal.signal(signal.SIGTERM, handler_stop_signals)


""" Main """
def main():
    
    log.info('otrrentworker start main....')
    
    """ log configuration in debug mode """
    if config['APPLICATION_LOG_LEVEL'] == 'DEBUG':
        for key, value in config.items():   
            log.debug('otrrentworker configuration: {} = {!s}'.format(key, value))

    """ run until stopsignal """
    while not stopsignal:
        if config['APPLICATION_ENVIRONMENT'] == 'Development':
            schedule.run_all()
        else:
            schedule.run_pending()
        time.sleep(60)

    """ goodby """ 
    log.info('otrrentworker service terminated. Goodby!')

""" run main if not imported """
if __name__ == '__main__':
    main()
