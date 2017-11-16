""" imports & globals """
import logging
import logging.handlers
import signal
import schedule
import time
import subprocess
import os

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

""" start Transmission daemon """
def start_transmission():
    try:      
        """ create transmission-log """
        if not os.path.exists('/usr/log/transmission.log'):
            call = 'touch /usr/log/transmission.log'      
            process = subprocess.run(call, shell=True, check=True, stdout=subprocess.PIPE , stderr=subprocess.PIPE)        
            call = 'chown -R debian-transmission:debian-transmission /usr/log'      
            process = subprocess.run(call, shell=True, check=True, stdout=subprocess.PIPE , stderr=subprocess.PIPE)

        """ update ACL for transmission access """
        call = 'chown -R debian-transmission:debian-transmission ' + config['APPLICATION_PATH_TORRENTS'] 
        process = subprocess.run(call, shell=True, check=True, stdout=subprocess.PIPE , stderr=subprocess.PIPE)        
        call = 'chown -R debian-transmission:debian-transmission ' + config['APPLICATION_PATH_OTRKEYS']
        process = subprocess.run(call, shell=True, check=True, stdout=subprocess.PIPE , stderr=subprocess.PIPE)
        call = 'chown -R debian-transmission:debian-transmission ' + config['APPLICATION_PATH_VIDEOS']   
        process = subprocess.run(call, shell=True, check=True, stdout=subprocess.PIPE , stderr=subprocess.PIPE)

        """ restart transmission service """
        call = 'service transmission-daemon start'
        log.debug(call)        
        process = subprocess.run(call, shell=True, check=True, stdout=subprocess.PIPE , stderr=subprocess.PIPE)
        time.sleep(5)
        log.info('init transmission-deamon finished. Returns {!s}'.format(process.stdout.decode(encoding='utf-8')))
        return True

    except subprocess.CalledProcessError as e:
        log.error('init transmission-deamon failed with cmd:{!s} because {!s}'.format(e.cmd, e.stderr))
        return False


""" Main """
def main():
    log.info('otrrentworker start main in {} environment....'.format(config['APPLICATION_ENVIRONMENT']))

    """ initiate transmission-deamon """
    daemonstarted = True
    if not config['APPLICATION_ENVIRONMENT'] in ['Development']:
        daemonstarted = start_transmission()      
    
    if daemonstarted:
        """ schedule workers """
        if config['APPLICATION_ENVIRONMENT'] == 'Development':
            schedule.every(1).minutes.do(runetl, config, log)

            """ log configuration in debug mode """
            for key, value in config.items():   
                log.debug('otrrentworker configuration: {} = {!s}'.format(key, value))

        elif config['APPLICATION_ENVIRONMENT'] == 'Test':
            schedule.every(1).minutes.do(runworker, config, log)
            schedule.every(1).hours.do(runetl, config, log)
            
        else:
            schedule.every(5).minutes.do(runworker, config, log)
            schedule.every().day.at("12:00").do(runetl, config, log)
            schedule.every().day.at("00:00").do(runetl, config, log)


        """ run until stopsignal """
        while not stopsignal:
            schedule.run_pending()
            time.sleep(1)

    """ goodby """ 
    log.info('otrrentworker service terminated. Goodby!')

""" run main if not imported """
if __name__ == '__main__':
    main()

