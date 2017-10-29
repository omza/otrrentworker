""" imports & globals """

""" import worker push, decode, download """
from worker.pushvideo import do_pushvideo_queue_message
from worker.pushtorrent import do_pushtorrent_queue_message

def runworker(config, log):
    """ run etl  """ 
    log.debug('try running otrrentworkers...')

    do_pushtorrent_queue_message(config, log)
    do_pushvideo_queue_message(config, log)

    log.info('successfully run otrrentworkers!')
    pass


