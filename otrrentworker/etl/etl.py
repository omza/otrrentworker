""" imports & globals """
import urllib.request
import csv
import os
from datetime import datetime, date, timedelta

""" azure storage repositories """
from azurestorage import db
from azurestorage.wrapper import StorageTableCollection
from azurestorage.tablemodels import Genre, Recording, Torrent

from helpers.helper import safe_cast

def import_otrgenres(config, log) -> StorageTableCollection:
    """ import genres csv into azure storage table """
    log.debug('try to import genres...')

    """ load Genres """
    db.register_model(Genre())
    Genres = StorageTableCollection('genres', "PartitionKey eq 'all'")
    Genres = db.query(Genres)

    
    if len(Genres) == 0:
        """ if genres are empty """           
        if not os.path.exists('genre.csv'):
                with urllib.request.urlopen('https://www.onlinetvrecorder.com/epg/genres.csv') as response:
                    genrecsv = response.read()
                    with open('genre.csv', 'wb') as ofile:
                        ofile.write(genrecsv)
 
        with open('genre.csv', 'r') as csvfile:
            reader = csv.DictReader(csvfile, dialect='excel', delimiter=';')
            fieldnames = reader.fieldnames
            rows = [row for row in reader]
            for row in rows:
                db.insert(Genre(Genre_Id=row['Nummer'], Genre=row['Kategorie']))


        os.remove('genre.csv')
        log.info('genres successfully imported')
    
        Genres = db.query(Genres)
    
    else:
        """ genres are not empty """
        log.info('genres already imported')
    
    return Genres

    pass

def import_otrepg(date, genres:StorageTableCollection, config, log):
    """ import otr epg for date into database:
        date:Str = Date a in dd.mm.yyyy to import

        1) check if entries for date exists
        2) if not then 
            a) download epg csv file from otr
            b) for all egp entries in csv try add to table storage
    """
    
    PartitionKey = date.strftime('%Y_%m_%d')
    csvfile = 'epg_' + PartitionKey + '.csv'
    log.debug('try to import epg csvfile: {!s} ...'.format(csvfile))

    db.register_model(Recording())

    if db.table_isempty(Recording._tablename, PartitionKey):
        try:
            if not os.path.exists(csvfile):
            
                with urllib.request.urlopen('https://www.onlinetvrecorder.com/epg/csv/'+csvfile) as response:
                    epgcsv = response.read()
                    with open(csvfile, 'wb') as ofile:
                        ofile.write(epgcsv)
                    log.info('download epg file successfull: {}'.format(csvfile))
            else:
                 log.info('epg already downloaded: {}'.format(csvfile))
        except:
            log.exception('Download egp csv:')
            return

        
 
        try:
            with open(csvfile, 'r', encoding='utf8', errors='ignore') as epgcsv:
                reader = csv.DictReader(epgcsv, dialect='excel', delimiter=';')
                fieldnames = reader.fieldnames
                rows = [row for row in reader]

                for row in rows:
                    row['PartitionKey'] = PartitionKey
                    row['RowKey'] = row['Id']

                    """ get genre """
                    genre = Genre(PartitionKey='all', RowKey=str(row['genre_id']))
                    if not genre:
                        row['genre'] = 'Sonstiges'
                    else:
                        row['genre'] = genre.Genre

                    tmp = Recording(**row)
                    db.insert(tmp)

            os.remove(csvfile)

        except:
            log.exception('Import epg csv data:')
            return

        log.info('import epg file successfull: {}'.format(csvfile))
    
    else:
        log.info('epg csv file {} already imported.'.format(csvfile))

def update_toprecordings(config, log):
    """ Rufe alle top bewerteten otr Aufzeichnungen ab: 
            https://www.onlinetvrecorder.com/v2/?go=list&tab=toplist&tlview=all&listid=104&start=0
        in 20er Paketen wird der content durchsucht und bei hohen Bewertungen das Recording in eine neue Partition verschoben
    """
    log.debug('try to update toprecordings webcontent...')
    stopflag = False
    start = 0

    toplist = []
    db.register_model(Recording())

    while not stopflag:

        """ download webcontent into content"""
        with urllib.request.urlopen('https://www.onlinetvrecorder.com/v2/?go=list&tab=toplist&tlview=all&listid=104&start=' + str(start)) as response:
            content = response.read()
        
        """ für jeden Eintrag in ID= searchrow """
        content = str(content.decode('utf-8', 'ignore')).split("<tr id='serchrow")
        for index in range(1,len(content)):
            lines = content[index].split('<td oncontextmenu="showNewTabMenu(')
            
            """ epg id """
            try:
                epg_id = lines[1].split(',')[0]
                rating = lines[8].split('Beliebtheit: ')[1].split("'")[0]
                previewimagelink = lines[10].split('<img src=')[1].split(' width=')[0]
                primarykey = datetime.strptime(lines[4].split('>')[1].split('<')[0], '%d.%m.%y').date().strftime('%Y_%m_%d')
                log.debug('parsed recording: {} with rating: {} and preview = {}'.format(epg_id, rating, previewimagelink))

            except:
                log.error('parsing not possible {!s}'.format(lines))

            if rating in ['sehr hoch', 'hoch']:
                top = db.get(Recording(PartitionKey = primarykey, RowKey = epg_id))  
                if not top is None:           
                    top.rating = rating
                    top.previewimagelink = previewimagelink
                    top.PartitionKey = 'top'
                    db.insert(top)
                    log.info('recording {} moved or is already moved successfully ({}, {!s}, at {})'.format(epg_id,top.titel, top.beginn, top.sender))
                else:
                    log.info('epg not found: {} with rating: {} and preview = {}'.format(epg_id, rating, previewimagelink)) 

            else:
                stopflag = True

                
        start = start + 20

    log.info('toprecordings successfully retireved!')

def update_torrents(startdate:date, config, log):
    """
        rufe alle torrents der letzten 8 Tage ab und ordne diese einem top recording zu
        https://www.onlinetvrecorder.com/v2/?go=tracker&search=&order=ctime%20DESC&start=0
    """
    log.debug('try to update torrents webcontent...')
    stopflag = False
    start = 0

    torrentlist = []
    db.register_model(Torrent())

    while not stopflag:

        """ download webcontent into content"""
        with urllib.request.urlopen('https://www.onlinetvrecorder.com/v2/?go=tracker&search=&order=ctime%20DESC&start=' + str(start)) as response:
            content = response.read()
        
        """ für jeden Eintrag in ID= searchrow """
        content = str(content.decode('utf-8', 'ignore')).split(' class="bordertable">')[1].split('</table>')[0].split('</tr>')
        for index in range(1, len(content)-1):
            lines = content[index].split('</td>')
            
            """ parse data from entry """
            torrentlink = lines[1].split("href='")[1].split("'")[0]
            torrentfile = lines[1].split(torrentlink + "'>")[1].split('</a>')[0]
            finished = safe_cast(lines[2].split('>')[1].split('</td>')[0],int,0)
            loading = safe_cast(lines[3].split('>')[1].split('</td>')[0],int,0)
            loaded = safe_cast(lines[4].split('>')[1].split('</td>')[0],int,0)
            
            fileparts = torrentfile.split(' ')     
            beginn = safe_cast(fileparts[len(fileparts)-4] + ' ' + fileparts[len(fileparts)-3] + '-00', datetime, None, '%y.%m.%d %H-%M-%S')
            sender = fileparts[len(fileparts)-2]
            
            if beginn.date() >= startdate:
                
                """ update list """
                torrent = {}
                torrent['TorrentLink'] = torrentlink
                torrent['TorrentFile'] = torrentfile
                torrent['finished'] = finished
                torrent['loading'] = loading
                torrent['loaded'] = loaded
                torrent['beginn'] = beginn
                torrent['sender'] = sender.replace(' ', '').lower()
                
                resolution = ''
                resolution = torrentlink.split('TVOON_DE')[1].split('otrkey.torrent')[0] 

                if resolution == ('.mpg.HD.avi.'):
                    """ TVOON_DE.mpg.HD.avi.otrkey.torrent"""
                    resolution = 'HD'
                    
                elif resolution == ('.mpg.HQ.avi.'):
                    """ _TVOON_DE.mpg.HQ.avi.otrkey.torrent"""
                    resolution = 'HQ'
                    
                elif resolution == ('.mpg.avi.'):
                    """ DIVX _TVOON_DE.mpg.avi.otrkey.torrent """
                    resolution = 'DIVX'
                    
                elif resolution == ('.mpg.mp4.'):
                    """ MP4  0_TVOON_DE.mpg.mp4.otrkey.torrent """
                    resolution = 'MP4'
                    
                elif resolution == ('.mpg.HD.ac3.'):
                    """ f1_130_TVOON_DE.mpg.HD.ac3.otrkey.torrent """
                    resolution = 'HD.AC3'
                    
                else:
                    resolution = 'AVI'
                    
                torrent['Resolution'] = resolution


                torrentlist.append(torrent)
                #log.debug('parsed torrent: {} in {} recorded at {!s} on {}'.format(torrentfile, resolution, beginn, sender))

            else:
                stopflag = True
                break
                
        start = start + 50

    log.info('{!s} torrents successfully retrieved...'.format(len(torrentlist)))

    """ retrieve epg id from top recordings """
    tops = StorageTableCollection('recordings', "PartitionKey eq 'top'")
    tops = db.query(tops)

    for top in tops:
        torrents = [item for item in torrentlist if item['beginn'].strftime('%y.%m.%d %H-%M-%S') == top.beginn.strftime('%y.%m.%d %H-%M-%S') and item['sender'] == top.sender.replace(' ', '').lower()]
        log.debug('filterded {!s} torrents for top recording {}'.format(len(torrents),top.titel))

        if len(torrents) >= 1:
            for torrent in torrents:
                db.insert(Torrent(Id = top.Id, **torrent))
        else:
            db.delete(Torrent(Id = top.Id, **torrent))
            db.delete(Recording(**top))

def housekeeping(date, config, log):
    """ housekeeping epg for date into database:
        date:Str = Date a in dd.mm.yyyy to import
    """

    PartitionKey = date.strftime('%Y_%m_%d')
    log.debug('housekeeping: try to delete all epg entries with Partitionkey: {!s} ...'.format(PartitionKey))

    """ load Genres """
    epgs = StorageTableCollection('recordings', "PartitionKey eq '"+ PartitionKey +"'")
    epgs = db.query(epgs)

    for epg in epgs:
        db.delete(epg)

    log.info('housekeeping finished for Partitionkey: {!s} ...'.format(PartitionKey))

    pass





