""" imports & globals """
from datetime import datetime, date, timedelta

""" run worker etl """
from etl.etl import import_otrepg, import_otrgenres, update_toprecordings, update_torrents
#from helpers.helper import safe_cast

def runetl(config, log):
    """ run etl  """ 
    log.info('run ETL')

    genres = import_otrgenres(config, log)

    """ loop back for 10 days and import"""
    iterdate = datetime.now().date() - timedelta(days=10)
    startdate = datetime.now().date() - timedelta(days=8)
    enddate = datetime.now().date() - timedelta(days=1 )
    while (iterdate <= enddate):             
        if (iterdate < startdate):
            """ housekeeping(iterdate) """
        else:
            import_otrepg(iterdate, genres, config, log)
            pass

        iterdate = iterdate + timedelta(days=1)

    update_toprecordings(config, log)

    update_torrents(startdate, config, log)
            
    log.info('next runtime ETL in {!s} seconds at {!s}'.format(config['APPLICATION_ETL_INTERVAL'], nextrun))

    pass

