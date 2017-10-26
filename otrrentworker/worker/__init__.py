""" imports & globals """

""" import worker push, decode, download """
from worker.push import processpushqueue

def runworker(config, log):
    """ run etl  """ 
    log.debug('try running otrrentworkers...')

    processpushqueue(config, log)

    log.info('successfully run otrrentworkers!')
    pass


