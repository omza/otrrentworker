""" Initialize azure storage repository """

from config import config

from azurestorage.wrapper import StorageTableContext, StorageQueueContext
db = StorageTableContext(**config)
queue = StorageQueueContext(**config)




