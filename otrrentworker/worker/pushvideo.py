""" imports & globals """
import os
from sys import stdout, stderr
import configparser
import re
import urllib
import fnmatch
from datetime import datetime
import subprocess

""" azure storage repositories """
from azurestorage import (
    queue,
    db
    )
from azurestorage.queuemodels import PushVideoMessage
from azurestorage.tablemodels import History

""" import logic and helpers """
from helpers.ftp import ftp_upload_file2
from helpers.logic import (
    download_fromurl, 
    get_torrentfile
    )

""" download cutlist file """
def get_cutlist(source_file, video_file, temp_path, log):
    log.debug('retrieve cutlist for {} file!'.format(source_file))

    try:
        cutlist_file = None

        """ Is cutlist already in tmp folder ? """
        pattern = str(video_file).split('_TVOON_')[0] + '*.cutlist'
            
        match = fnmatch.filter(os.listdir(temp_path), pattern)
        for file in match:
            cutlist_file = os.path.join(temp_path, file)
            log.info('Already existing cutlist: {}'.format(cutlist_file))
            break

        if cutlist_file is None:
            """ download list of cutlists into string """
            url = 'http://www.onlinetvrecorder.com/getcutlistini.php?filename=' + source_file
            response = urllib.request.urlopen(url)
            content = str(response.read().decode('utf-8', 'ignore'))

            """ parse list of cutlists """
            cutlists = configparser.ConfigParser(strict=False, allow_no_value=True)
            cutlists.read_string(content)
    
            """ download the first cutlist to file in /tmp """
            if cutlists.has_option('FILE1','filename'):
                curlist_url = cutlists.get('FILE1','filename')
                cutlist_file = os.path.join(temp_path, os.path.basename(curlist_url))
                download_fromurl(curlist_url, cutlist_file)
            
                """ success """
                log.info('downloaded cutlist to {}...'.format(cutlist_file))
                    
            else:
                log.info('no cutlist for {} file!'.format(source_file))

        return cutlist_file                  

    except:
        log.exception('Exception Traceback:')
        return None

""" decode otrkey file"""
def decode(log, otr_user, otr_pass, use_cutlists, source_fullpath, video_path, cutlist_fullpath = None):
    try:     
        call = 'otrdecoder -i ' + source_fullpath + ' -o ' + video_path + ' -e ' + otr_user + ' -p ' + otr_pass + ' -f'   
        if not cutlist_fullpath is None:
                call = call + ' -C ' + cutlist_fullpath         
        log.debug('decode call: {} !'.format(call))

        process = subprocess.Popen(call, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        process.wait()
        
        """ decoding successful ? """
        if process.returncode != 0:
            return False, 'decoding failed with code {!s} and output {!s}'.format(process.returncode, process.stderr.read())
        else:
            log.info('Decoding succesfull with returncode {!s}.'.format(process.returncode))
            return True, None

    except Exception as e:
        log.exception('Exception Traceback:')
        return False, e

""" parse transmission-remote status """
def get_transmissionstatus(log) -> list:

    try:
        transmissionstatus = []

        """ check running transmission downloads """
        call = 'transmission-remote -n transmission:transmission -l'       
        process = subprocess.run(call, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)                    
                    
        """ parse stdout lines for download status 
            ID     Done       Have  ETA           Up    Down  Ratio  Status       Name
            Sum:              None               0.0     0.0
        """
        log.debug('{}'.format(process.stdout.decode(encoding='utf-8')))

        for line in process.stdout.decode(encoding='utf-8').splitlines():          
            if len(line) >= 71:
                transmissionSingleStatus = {}
                
                transmissionSingleStatus['sID'] = line[:5].strip()
                transmissionSingleStatus['ID'] = re.sub(r"\D", "", line[:5].strip())
                transmissionSingleStatus['Done'] = line[6:11].strip()
                transmissionSingleStatus['ETA'] = line[22:32].strip()
                transmissionSingleStatus['Status'] = line[57:69].strip()
                transmissionSingleStatus['Name'] = line[70:].strip()

                log.debug('torrent status {!s}'.format(transmissionSingleStatus))

                transmissionstatus.append(transmissionSingleStatus)
               
        return transmissionstatus

    except subprocess.CalledProcessError as e:
        log.error('cmd {!s} failed because {!s}, {!s}'.format(e.cmd, e.stderr, e.stdout))
        return []
    

""" delete torrent from transmission queue """


""" restart torrent in transmission queue """



""" process push queue """
def do_pushvideo_queue_message(config, log):
    """ retrieve and process all visible download queue mess ages      
        - if link is url then download torrentfile
            ---------------------------------------------------------------------
            1) if videofile is in place: 
                1a) push video to ftp 
                1b) delete videofile, otrkeyfile, torrentfile
                1c) delete queue message
            2) OR if otrkeyfile is in place 
                2a) init decodingprocess to videofile
            3) ELSE if transmission job is not running
                3a) add transmission torrent
    """
    queue.register_model(PushVideoMessage())
    db.register_model(History())

    if config['APPLICATION_ENVIRONMENT'] in ['Development', 'Test']:
        queuehide = 60
    else:
        queuehide = 5*60

    """ housekeeping array of files and transmission-queues to be deleted """
    houskeeping = []
    housekeepingTransmission = []

    """ get transmission status """
    transmissionstatus = get_transmissionstatus(log)

    """ loop all push queue messages """
    message = queue.get(PushVideoMessage(), queuehide)
    while not message is None:

        """ get history entry for message for an status update """
        history = History(PartitionKey='video', RowKey = message.id)
        db.get(history)
        if not db.exists(history):
            history.created = datetime.now()
            history.epgid = message.epgid
            history.sourcefile = message.videofile
        #log.debug('{!s}'.format(history.dict()))

        """ get single transmission download status """
        downloadstatus = [element for element in transmissionstatus if element['Name'] == message.otrkeyfile]
        if downloadstatus != []:
            downloadstatus = downloadstatus[0]
        else:
            downloadstatus = None
        #log.debug('{!s}'.format(downloadstatus))

        if message.sourcelink in ['', 'string']:
            """ no sourcelink ? """
            """ delete queue message and tmp file """
            queue.delete(message)
            history.status = 'deleted'

        else:
            """ process push video """          
            try:
                localvideofile = os.path.join(config['APPLICATION_PATH_VIDEOS'], message.videofile)
                localotrkeyfile = os.path.join(config['APPLICATION_PATH_OTRKEYS'], message.otrkeyfile)
                message.sourcefile, localtorrentfile = get_torrentfile(message.sourcelink, config['APPLICATION_PATH_TORRENTS'])
            
                if os.path.exists(localvideofile):
                    """ 1) videofile is in place: 
                        1a) push video to ftp 
                        1b) delete videofile, otrkeyfile, torrentfile
                        1c) delete queue message """

                    """ 1a) push video to ftp """
                    uploaded, errormessage =  ftp_upload_file2(log, message.server, message.port, message.user, message.password, message.destpath, message.videofile, localvideofile)
                    if uploaded:
                        """ 1b) delete videofile, otrkeyfile, torrentfile """
                        houskeeping.append(localvideofile)
                        houskeeping.append(localotrkeyfile)
                        houskeeping.append(localtorrentfile)

                        """ 1c) delete queue message """
                        queue.delete(message)

                        log.info('push video queue message {!s} for {!s} successfully processed!'.format(message.id, message.videofile))
                        history.status = 'finished'

                    else:
                        raise Exception('push failed because {}'.format(errormessage))

                elif os.path.exists(localotrkeyfile):
                    """ 2) OR if otrkeyfile is in place
                        2a) init decodingprocess to videofile 
                        2b) delete transmission queue """ 

                    """  2a) init decodingprocess to videofile """
                    if message.usecutlist:
                        localcutlistfile = get_cutlist(message.otrkeyfile, message.videofile, config['APPLICATION_PATH_TMP'], log)
                    else:
                        localcutlistfile = None

                    decoded, errormessage = decode(log, 'omza@gmx.de', message.otrpassword, message.usecutlist, localotrkeyfile, config['APPLICATION_PATH_VIDEOS'], localcutlistfile)
                    if not decoded:
                        raise Exception(errormessage)
                    else:
                        houskeeping.append(localcutlistfile)
                        if not downloadstatus is None:
                            housekeepingTransmission.append(downloadstatus)
                        
                        log.info('decoding otrkeyfile {!s} successfully processed!'.format(message.otrkeyfile))
                        history.status = 'decoded'
                                                                                                                                                             
                else:
                    """ 3) ELSE if transmission job is not running
                        3a) add transmission torrent """

                    if not downloadstatus is None:
                        
                        history.status = downloadstatus['Status'] + ' ' + downloadstatus['Done'] + ' (ETA ' + downloadstatus['ETA'] + ')'
                        log.info('otrkeyfile {!s} {}'.format(message.otrkeyfile, history.status))
        
                    else:
                        """ 3a) add transmission torrent """
                        if os.path.exists(localtorrentfile):
                            downloaded = True
                        else:
                            downloaded, errormessage = download_fromurl(message.sourcelink, localtorrentfile)
                    
                        if downloaded: 
                            log.info('downloading torrentfile {!s} successfully initiated!'.format(message.sourcefile))
                            history.status = 'download started'

                        else:
                            raise Exception(errormessage)

  
            except Exception as e:
                if isinstance(e, subprocess.CalledProcessError):
                    errormessage = 'cmd {!s} failed because {!s}, {!s}'.format(e.cmd,e.stderr, e.stdout)
                else:
                    errormessage = e
                log.exception('push video failed because {!s}'.format(errormessage))
                history.status = 'error'

                """ delete message after 3 tries """
                if (not config['APPLICATION_ENVIRONMENT'] == 'Development') and (message.dequeue_count >= 3):
                    queue.delete(message)
                    history.status = 'deleted'
 
        """ update history entry """
        history.updated = datetime.now()
        db.merge(history)
        
        """ next message """
        message = queue.get(PushVideoMessage(), queuehide)

    """ housekeeping temporary files """
    for file in houskeeping:
        if os.path.exists(file):
            os.remove(file)

    """ houskeeping torrent queue """
    for torrentsinglestate in housekeepingTransmission:
        call = 'transmission-remote -t ' + torrentsinglestate['ID'] + ' -r'      
        process = subprocess.run(call, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        log.debug('{} finished with {}'.format(call, process.stdout.decode(encoding='utf-8')))

    for torrentsinglestate in transmissionstatus:
        """ restart queue entries """
        if torrentsinglestate['Status'] == 'Stopped':
            call = 'transmission-remote -t ' + torrentsinglestate['ID'] + ' -s'      
            process = subprocess.run(call, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            log.debug('{} finished with {}'.format(call,process.stdout.decode(encoding='utf-8')))

    pass