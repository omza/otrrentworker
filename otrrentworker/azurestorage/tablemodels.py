""" imports & Gloabls """
import datetime

""" import wrapper class and base model """
from azurestorage.wrapper import (
    StorageTableModel, 
    StorageTableCollection
    )


class Torrent(StorageTableModel):
    _tablename = 'torrents'
    _dateformat = '%d.%m.%Y'
    _datetimeformat = '%d.%m.%Y %H:%M:%S'

    Id = 0
    Resolution = ''
    TorrentFile = ''
    TorrentLink = ''
    finished = 0
    loading = 0 
    loaded = 0

    def __setPartitionKey__(self):
        self.PartitionKey = self.Id
        return super().__setPartitionKey__()

    def __setRowKey__(self):
        self.RowKey = self.Resolution
        return super().__setRowKey__()

class Recording(StorageTableModel):
    _tablename = 'recordings'
    _dateformat = '%d.%m.%Y'
    _datetimeformat = '%d.%m.%Y %H:%M:%S'
    
    Id = 0
    beginn = datetime.datetime.strptime('01.01.1900 00:00:00', _datetimeformat)
    ende  = datetime.datetime.strptime('01.01.1900 00:00:00', _datetimeformat)
    dauer = 0
    sender = ''
    titel = ''
    typ = ''
    text = ''
    genre_id = 0
    genre = ''                                                                                               
    fsk = ''
    language = ''
    weekday = ''
    zusatz = ''
    wdh = ''
    downloadlink = ''
    infolink = ''
    programlink = ''
    rating = ''
    previewimagelink = ''
    Torrents = StorageTableCollection(_tablename)

    def __setPartitionKey__(self):
        self.PartitionKey = self.beginn.strftime('%Y_%m_%d')
        return super().__setPartitionKey__()

    def __setRowKey__(self):
        self.RowKey = str(self.Id)
        return super().__setRowKey__()

    def __setCollections__(self):
        self.Torrents = StorageTableCollection('torrents', "PartitionKey eq '{}'".format(self.RowKey))
        return super().__setCollections__()

class Genre(StorageTableModel):   
    _tablename = 'genres'                       
    Genre_Id = 0
    Genre = ''

