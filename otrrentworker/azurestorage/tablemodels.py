""" imports & Gloabls """
import datetime

from azure.common import AzureException 
from azure.storage.table import Entity, TableService, EntityProperty, EdmType

from azurestorage.wrapper import StorageTableModel, StorageTableCollection
from helpers.helper import safe_cast

""" configure logging """
from config import log

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


class Genres(StorageTableCollection):
    _tablename = 'genres'
     
    _collection = []

    def __init__(self, tableservice, filter):
        """Initializes the GenresList with the specified settings dict.
        Required settings are:
         - db = Azure Table Storage tableservice
        """
        self._tableservice = tableservice
        self._tablename = self.__class__._tablename
        self._filter = filter
        self._collection = []
        self.__loadcollection__()

    def __loadcollection__(self):
        allentities = self._tableservice.query_entities(self._tablename, self._filter)
        for entity in allentities:
            self._collection.append(entity)

    def getgenrefromid(self, id):
        """ has to be overwritten """
        for genre in self._collection:
            if genre['Genre_Id'] == safe_cast(id, int,0):
                return genre['Genre']
                break
        return 'Sonstiges'
