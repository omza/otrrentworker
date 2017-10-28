""" imports & globals """
import os
from sys import stdout, stderr
import subprocess

""" azure storage repositories """
from azurestorage import queue
from azurestorage.queuemodels import DownloadMessage


def initbittorrent(torrentlink, otrkeypath):
    """ initiate bittorrent client to download torrent """
    try:
        
        call = 'transmission-cli -d 400 -er -u 25 -w ' + otrkeypath + ' ' + torrentlink 
        
        process = subprocess.Popen(call, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        process.wait()

        """ download successful ? """
        if process.returncode != 0:
            return False, 'download otrkey failed with code {!s} and output {!s}'.format(process.returncode, process.stderr.read())
                    
        else:
            return True, None
            
    except Exception as e:
        return False, 'download otrkey {!s} failed with {!s}'.format(torrentlink, e) 

""" process push queue """
def processdownloadqueue(config, log):
    """ retrieve and process all visible download queue messages      
        - if link is url then download torrentfile
        - initiate bittorrent client to download otrkey file
    """
    queue.register_model(DownloadMessage())
    if config['APPLICATION_ENVIRONMENT'] in ['Development', 'Test']:
        queuehide = 1
    else:
        queuehide = 5*60

    """ loop all push queue messages """
    message = queue.get(DownloadMessage(), queuehide)
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

            """ 1) download torrent to local tmp folder 
            filename, localfile = get_torrentfile(message.sourcelink, config['APPLICATION_PATH_TORRENTS'])
            if (not filename is None) and (not localfile is None):
                downloaded, errormessage = download_fromurl(message.sourcelink, localfile)

                if downloaded:   """          
            """ 2) initiate download with torrent client """
            bittorrent, errormessage = initbittorrent(message.sourcelink, config['APPLICATION_PATH_OTRKEYS'])

            if bittorrent:
                
                """ 4) delete queue message """
                queue.delete(message)
                log.info('Download queue message {!s} for Torrent {!s} successfully processed'.format(message.id, filename))
            
            if not errormessage is None:
                """ delete message after 3 tries """
                log.error('push failed because {}'.format(errormessage))
                if (not config['APPLICATION_ENVIRONMENT'] in ['Development']) and (message.dequeue_count >= 3):
                    queue.delete(message)
                
        """ next message """
        message = queue.get(DownloadMessage(), queuehide)

    pass