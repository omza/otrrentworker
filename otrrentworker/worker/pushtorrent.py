""" imports & globals """
import os
from datetime import datetime

""" azure storage repositories """
from azurestorage import (
    queue,
    db
    )
from azurestorage.queuemodels import PushMessage
from azurestorage.tablemodels import History

""" import logic and helpers """
from helpers.ftp import ftp_upload_file
from helpers.logic import (
    download_fromurl, 
    get_torrentfile
    )

""" process push queue """
def do_pushtorrent_queue_message(config, log):
    """ retrieve and process all visible push queue messages      
        - if link is local check if file exist then push to ftp endpoint
        - if link is url then download torrentfile and push to endpoint
    """
    queue.register_model(PushMessage())
    db.register_model(History())

    if config['APPLICATION_ENVIRONMENT'] in ['Development', 'Test']:
        queuehide = 1
    else:
        queuehide = 5*60


    """ loop all push queue messages """
    message = queue.get(PushMessage(), queuehide)
    while not message is None:

        """ get history entry for message for an status update """
        history = History(PartitionKey='torrent', RowKey = message.id)
        db.get(history)
        
        if message.sourcelink in ['', 'string']:
            """ no sourcelink ? """
            """ delete queue message and tmp file """
            queue.delete(message)        

        else:
            """ push torrentfile
                ---------------------------------------------------------------------
                1) download torrent to local tmp folder
                2) pushfile to ftp
                3) delete torrent from local tmp folder
                4) delete queue message
            """      

            """ 1) download torrent to local tmp folder """
            filename, localfile = get_torrentfile(message.sourcelink, config['APPLICATION_PATH_TMP'])
            if (not filename is None) and (not localfile is None):
                downloaded, errormessage = download_fromurl(message.sourcelink, localfile)

                if downloaded:             
                    """ 2) pushfile to ftp """
                    uploaded, errormessage =  ftp_upload_file(log, message.server, message.port, message.user, message.password, message.destpath, filename, localfile)

                    if uploaded:
                        """ 3) delete torrent from local tmp folder, 
                            4) delete queue message 
                        """
                        queue.delete(message)
                        if os.path.exists(localfile): 
                            os.remove(localfile)
            
            if not errormessage is None:
                """ delete message after 3 tries """
                log.error('push failed because {}'.format(errormessage))
                history.status = 'error'
                if (not config['APPLICATION_ENVIRONMENT'] == 'Development') and (message.dequeue_count >= 3):
                    queue.delete(message)
                    history.status = 'deleted'
                if os.path.exists(localfile): 
                    os.remove(localfile)
        
        """ update history entry """
        history.updated = datetime.now()
        db.merge(history)

        """ next message """
        message = queue.get(PushMessage(), queuehide)

    pass

