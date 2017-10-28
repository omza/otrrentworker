""" import & globals """
import ftplib

""" test connection """
def test_ftpconnection(server, port, user, password, path):
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
def ftp_upload_file(server, port, user, password, path, filename, localfile):
    try:
                
        """ login to ftp server """
        ftp = ftplib.FTP()

        ftp.connect(server, port)
        ftp.login(user=user, passwd=password)
      
        """ check fpt_path exist ? """
        ftp.cwd(path)

        """ upload file """
        ftp.storbinary('STOR ' + filename, open(localfile, 'rb'))

        """ logout ftp session """
        ftp.quit()

        """ return """
        return True, None
                
    except ftplib.all_errors as e:
        return False, 'Error in ftp upload ({!s}:{!s}) = {!s}'.format(server, port, e)