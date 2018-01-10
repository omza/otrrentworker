""" imports & globals """
from datetime import datetime, date, timedelta

""" run worker etl """
from etl.etl import (
    import_otrepg, 
    import_otrgenres, 
    update_toprecordings, 
    update_torrents, 
    housekeeping
    )

def runetl(config, log):
    """ run etl  """ 
    log.info('run ETL')

    genres = import_otrgenres(config, log)

    """ loop back for 10 days and import"""
    iterdate = datetime.now().date() - timedelta(days=10)
    startdate = datetime.now().date() - timedelta(days=8)
    enddate = datetime.now().date()
    while (iterdate <= enddate):             
        if (iterdate < startdate):
            """ housekeeping(iterdate) """
            housekeeping(iterdate, config, log)        
            
        else:
            import_otrepg(iterdate, genres, config, log)

        iterdate = iterdate + timedelta(days=1)

    update_toprecordings(config, log)

    update_torrents(startdate, config, log)
            
    log.info('successfully run ETL and Houskeeping!')

    pass

