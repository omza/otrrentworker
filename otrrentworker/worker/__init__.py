""" imports & globals """

""" import worker push, decode, download """
from worker.download import processdownloadqueue
from worker.decode import processdecodequeue
from worker.push import processpushqueue

def runworker(config, log):
    """ run etl  """ 
    log.debug('try running otrrentworkers...')

    processdownloadqueue(config, log)
    processdecodequeue(config, log)
    processpushqueue(config, log)

    log.info('successfully run otrrentworkers!')
    pass


