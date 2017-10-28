""" imports & globals """
import os

""" azure storage repositories """
from azurestorage import queue
from azurestorage.queuemodels import DownloadMessage

""" import logic and helpers """
from helpers.ftp import ftp_upload_file
from helpers.logic import (
    download_fromurl, 
    get_torrentfile
    )

""" process push queue """
def processdownloadqueue(config, log):
    """ retrieve and process all visible download queue messages      
        - if link is url then download torrentfile
        - initiate bittorrent client to download otrkey file
    """
    queue.register_model(DownloadMessage())

    """ loop all push queue messages """
    message = queue.get(DownloadMessage(), 5*60)
    while not message is None:

        if message.sourcelink == '':
            """ no sourcelink ? """
            """ delete queue message and tmp file """
            queue.delete(message)        

        else:
            """ download torrentfile
                ---------------------------------------------------------------------
                1) download torrent to local torrent folder
                2) initiate download with torrent client
                3) delete torrent from local tmp folder
                4) delete queue message
            """      

            """ 1) download torrent to local tmp folder """
            filename, localfile = get_torrentfile(message.sourcelink, config['APPLICATION_PATH_TORRENTS'])
            if (not filename is None) and (not localfile is None):
                downloaded, errormessage = download_fromurl(message.sourcelink, localfile)

                if downloaded:             
                    """ 2) initiate download with torrent client """
                    bittorrent = True

                    if bittorrent:
                        """ 3) delete torrent from local tmp folder, 
                            4) delete queue message 
                        """
                        queue.delete(message)
                        if os.path.exists(localfile): 
                            os.remove(localfile)

                        log.info('Download queue message {!s} for Torrent {!s} successfully processed'.format(message.id, filename))
            
            if not errormessage is None:
                """ delete message after 3 tries """
                log.error('push failed because {}'.format(errormessage))
                if message.dequeue_count >= 3:
                    queue.delete(message)
                if os.path.exists(localfile): 
                    os.remove(localfile)
                
        """ next message """
        message = queue.get(DownloadMessage(), 5*60)

    pass