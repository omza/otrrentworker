""" imports & globals """
import logging
import logging.handlers
import signal
import schedule
import time
import subprocess

""" import config and workers """
from config import (
    config, 
    log
    )

from etl import runetl
from worker import runworker


""" handle sigterm and sigint """
stopsignal = False
def handler_stop_signals(signum, frame):
    global stopsignal
    stopsignal = True
signal.signal(signal.SIGINT, handler_stop_signals)
signal.signal(signal.SIGTERM, handler_stop_signals)


""" Main """
def main():
    log.info('otrrentworker start main in {} environment....'.format(config['APPLICATION_ENVIRONMENT']))

    """ initiate transmission-deamon """
    daemonstarted = True
    if not config['APPLICATION_ENVIRONMENT'] in ['Development']:
        try:      
            """ restart transmission service """
            call = 'service transmission-daemon start'
            log.debug(call)        
            process = subprocess.run(call, shell=True, check=True, stderr=subprocess.PIPE)
            time.sleep(5)

            """ configure download folder """
            call = 'transmission-remote -n transmission:transmission -w ' + config['APPLICATION_PATH_OTRKEYS']
            log.debug(call)
            process = subprocess.run(call, shell=True, check=True, stderr=subprocess.PIPE)

            """ restart downloading all pending torrents """
            call = 'transmission-remote -n transmission:transmission -s'
            log.debug(call)
            process = subprocess.run(call, shell=True, check=True, stderr=subprocess.PIPE)

            """ check running transmission downloads """
            call = 'transmission-remote -n transmission:transmission -l'       
            process = subprocess.run(call, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)                    
            torrents = '{!s}'.format(process.stdout)
            log.debug(torrents)

        except subprocess.CalledProcessError as e:
            log.error('init transmission-deamon failed with cmd:{!s} because {!s}'.format(e.cmd, e.stderr))
            daemonstarted = False            
    
    if daemonstarted:
        """ schedule workers """
        if config['APPLICATION_ENVIRONMENT'] in ['Development', 'Test']:
            schedule.every(5).minutes.do(runworker, config, log)
        else:
            schedule.every(5).minutes.do(runworker, config, log)
            schedule.every().day.at("00:30").do(runetl, config, log)

        """ log configuration in debug mode """
        if config['APPLICATION_ENVIRONMENT'] in ['Development', 'Test']:
            for key, value in config.items():   
                log.debug('otrrentworker configuration: {} = {!s}'.format(key, value))

        """ run until stopsignal """
        while not stopsignal:
            schedule.run_pending()
            time.sleep(1)

    """ goodby """ 
    log.info('otrrentworker service terminated. Goodby!')

""" run main if not imported """
if __name__ == '__main__':
    main()
