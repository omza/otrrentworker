""" import & globals """
import ftplib
import os

""" test connection """
def test_ftpconnection(server, port, user, password, path, log):
    try:
                
        """ login to ftp server """
        ftp = ftplib.FTP()

        ftp.connect(server, port)
        ftp.login(user=user, passwd=password)
      
        """ check fpt_path exist ? """
        ftp.cwd(path)

        """ logout ftp session """
        ftp.quit()

        """ return """
        return True, None
                
    except ftplib.all_errors as e:
        return False, 'Error in ftp login ({!s}:{!s}) = {!s}'.format(server, port, e)


""" ftp upload to server """
def ftp_upload_file(log, server, port, user, password, path, filename, localfile):
    try:
                
        """ login to ftp server """
        ftp = ftplib.FTP()
        ftp.set_pasv(True)
        ftp.connect(server, port, timeout=300)
        ftp.login(user=user, passwd=password)
        log.debug('login to ftp {!s}:{!s} succeeded'.format(server,port))
      
        """ check fpt_path exist ? """
        ftp.cwd(path)

        """ upload file """
        log.debug('upload file {} with {!s} size'.format(localfile, os.path.getsize(localfile)))
        if os.path.getsize(localfile) >= 1024:
            ftp.storbinary('STOR ' + filename, open(localfile, 'rb'), 1024, ftp_keepalive(log, ftp))
        else:
            ftp.storbinary('STOR ' + filename, open(localfile, 'rb'))

        log.debug('upload file {} to ftp {!s}:{!s} succeeded'.format(localfile, server,port))
        
        """ logout ftp session """
        ftp.quit()

        """ return """
        return True, None
                
    except ftplib.all_errors as e:
        return False, 'Error in ftp upload ({!s}:{!s}) = {!s}'.format(server, port, e)

def ftp_keepalive(log, ftp):
    try:
                
        """ send keepalive on command line """
        ftp.voidcmd('NOOP')
        log.debug('ftp keepalive')
                
    except ftplib.all_errors as e:
        log.error('Error send keepalive = {!s}'.format(e))