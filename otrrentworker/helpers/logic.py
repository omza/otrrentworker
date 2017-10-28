""" imports & globals """
import urllib
from urllib.parse import urlparse
import os

""" retrieve torrent filename from torrentlink """
def get_torrentfile(torrentlink, path):
    try:
        filename = os.path.basename(urlparse(torrentlink).path)
        fullpath = os.path.join(path, filename)
        return filename, fullpath

    except:
        return None, None


""" download file from url to local path """
def download_fromurl(url, localfile):
    try:
        if not os.path.exists(localfile):
            with urllib.request.urlopen(url) as response, open(localfile, 'wb') as out_file:
                data = response.read() # a `bytes` object
                out_file.write(data)
        return True, None

    except Exception as e:
        return False, 'download_fromurl failed ({!s}->{!s}) because {!s}'.format(url, localfile, e)

