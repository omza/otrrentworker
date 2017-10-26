""" imports & globals """
import ftplib
import urllib.request
import os

""" azure storage repositories """
from azurestorage import queue
from azurestorage.queuemodels import PushMessage

""" process push queue """
def processpushqueue(config, log):
    """ retrieve and process all visible push queue messages      
        - if link is local check if file exist then push to ftp endpoint
        - if link is url then download torrentfile and push to endpoint
    """
    queue.register_model(PushMessage())

    """ loop all push queue messages """
    message = queue.get(PushMessage(), 5*60)
    while not message is None:

        """ file is local ? """
        if message.sourcelink == '(local)':
            """ push videofile"""
            pass

        else:
            """ push torrentfile
                ---------------------------------------------------------------------
                1) download torrent to local tmp folder
                2) pushfile to ftp
                3) delete torrent from local tmp folder
                4) delete queue message
            """
            file_name = ''
            
            if message.sourcelink != '':
                try:
                    """ Download the file from `url` and save it locally under `file_name`: """
                    file_name = os.path.join(config['APPLICATION_PATH_TMP'], message.sourcefile)
                    if not os.path.exists(file_name):
                        with urllib.request.urlopen(message.sourcelink) as response, open(file_name, 'wb') as out_file:
                            data = response.read() # a `bytes` object
                            out_file.write(data)
                
                    """ login to ftp server """
                    ftp = ftplib.FTP()

                    ftp.connect(message.server, message.port)
                    ftp.login(user=message.user, passwd=message.password)
      
                    """ check fpt_path exist ? """
                    ftp.cwd(message.destpath)

                    """ move file """
                    ftp.storbinary('STOR ' + message.sourcefile, open(file_name, 'rb'))

                    """ logout ftp session """
                    ftp.quit()

                except Exception as e:
                    log.error('can not push torrentfile {} from path: {} because {!s}'.format(message.sourcelink, message.sourcefile, e))

            """ delete queue message and tmp file """
            queue.delete(message)
            if os.path.exists(file_name): 
                os.remove(file_name)

        """ next message """
        message = queue.get(PushMessage(), 5*60)

    pass

