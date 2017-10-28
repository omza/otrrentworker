""" imports & globals """

""" import worker push, decode, download """
from worker.push import processpushqueue
from worker.download import processdownloadqueue

def runworker(config, log):
    """ run etl  """ 
    log.debug('try running otrrentworkers...')

    processpushqueue(config, log)
    processdownloadqueue(config, log)

    log.info('successfully run otrrentworkers!')
    pass


