""" imports & globals """
import os, fnmatch
import subprocess
from sys import stdout, stderr
import configparser
import re
import urllib

""" azure storage repositories """
from azurestorage import queue
from azurestorage.queuemodels import DecodeMessage

""" import logic and helpers """
from helpers.ftp import ftp_upload_file
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


def decode(source_fullpath, log):
    """ decode file """
    log.debug('try to decode {}'.format(source_fullpath))                     
    try:     
        call = self.otrdecoder_executable + ' -i ' + source_fullpath + ' -o ' + self.temp_path + ' -e ' + self.otr_user + ' -p ' + self.otr_pass + ' -f'
                
        if self.use_cutlists:
            self.cutlist_fullpath = self.get_cutlist()
            if not self.cutlist_fullpath is None:
                    call = call + ' -C ' + self.cutlist_fullpath
                
        log.debug('decode call: {} !'.format(call))

        process = subprocess.Popen(call, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        process.wait()
        
        """ decoding successful ? """
        if process.returncode != 0:
            log.error('decoding failed with code {!s} and output {!s}'.format(process.returncode, process.stderr.read()))
                    
        else:
            log.info('Decoding succesfull with returncode {!s}.'.format(process.returncode))
            self.decoded = True

        except:
            log.exception('Exception Traceback:')

""" process push queue """
def processdecodequeue(config, log):
    """ retrieve and process all visible decode queue messages      
        1) if sourcefile .otrkey is in otrkeyfolder:
            2) check/download cutlist
            3) initiate otrdecoder
    """
    queue.register_model(DecodeMessage())
    if config['APPLICATION_ENVIRONMENT'] in ['Development', 'Test']:
        queuehide = 1
    else:
        queuehide = 5*60

    """ loop all push queue messages """
    message = queue.get(DecodeMessage(), queuehide)
    while not message is None:

        source_fullpath = os.path.join(config['APPLICATION_PATH_OTRKEYS'], message.otrkeyfile)

        if message.otrkeyfile in ['', 'string']:
            """ no sourcelink ? """
            """ delete queue message and tmp file """
            queue.delete(message)        

        elif os.path.exists(source_fullpath):
            """ decode otrkeyfile
                ---------------------------------------------------------------------
                1) download torrent to local torrent folder
                2) initiate download with torrent client
                3) delete torrent from local tmp folder
                4) delete queue message
            """

            log.info('Decode queue message {!s} for otrkey {!s} successfully processed'.format(message.id, message.otrkeyfile))

        """ next message """
        message = queue.get(DecodeMessage(), queuehide)

    pass
