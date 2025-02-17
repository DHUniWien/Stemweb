
import os
import time
import shutil
import logging
import datetime

from django.conf import settings
from .models import AlgorithmRun
from Stemweb.files.models import InputFile

logger = logging.getLogger('stemweb.algorithm_run')

def remove_oldresults_fs():
    """ removes results in file system (result files and result directories) which are older than settings.KEEP_RESULTS_DAYS """
    numdays = 60*60*24*int(settings.KEEP_RESULTS_DAYS)
    now = time.time()
    directory=os.path.join(settings.MEDIA_ROOT,"results/runs")
    logger = logging.getLogger('stemweb.algorithm_run')

    for root, dirs, _files in os.walk(directory):
        for d in dirs:
            timestamp = os.path.getmtime(os.path.join(root,d))
            if now-numdays > timestamp:
                try:
                    logger.info('older results than %s days found in file system: removing from %s ' % (settings.KEEP_RESULTS_DAYS, os.path.join(root,d)))
                    shutil.rmtree(os.path.join(root,d)) 
                except Exception as e:
                    #print e
                    logger.error('removing failed with error %s: ' % (e), exc_info=1)
                    pass
                else: 
                    logger.info('successfully removed')

def remove_oldresults_db():
    """ removes AlgorithmRun data in the database where the end time of the runs are older than settings.KEEP_RESULTS_DAYS.
        The django based db access method models.AlgorithmRun.delete() is used.
    """

    todaysDate = datetime.date.today()
    no_of_days = datetime.timedelta(days = int(settings.KEEP_RESULTS_DAYS)) 
    reference_date = todaysDate - no_of_days
    run_candidates = AlgorithmRun.objects.filter(end_time__lt=reference_date)   ### __lt: less than

    count = len(run_candidates)
    if count > 0:
        logger.info(f" Cleanup database: delete {count} runs/results from DB") 
    for run in run_candidates:
        logger.info(f"run-id {run.id}")
        run.delete()

def remove_oldinputs_fs():
    """ Removes input data files in file system (files and directories) which are older than settings.KEEP_INPUTS_DAYS 
        InputFile-folders below settings.MEDIA_ROOT are: files/csv/ for processed rhm data and 
                                                         files/nex/ for processed nj & nnet data. 
                                                         files/originalInputData/ for unprocessed input data (rhm, nkj nnet).
    """
    numdays = 60*60*24*int(settings.KEEP_INPUTS_DAYS)
    now = time.time()
    directory=os.path.join(settings.MEDIA_ROOT,"files")
    logger = logging.getLogger('stemweb.algorithm_run')

    for root, dirs, _files in os.walk(directory):
        for d in dirs:
            timestamp = os.path.getmtime(os.path.join(root,d))
            if now-numdays > timestamp:
                try:
                    logger.info('older files than %s days found in file system: removing from %s ' % (settings.KEEP_INPUTS_DAYS, os.path.join(root,d)))
                    shutil.rmtree(os.path.join(root,d)) 
                except Exception as e:
                    #print e
                    logger.error('removing failed with error %s: ' % (e), exc_info=1)
                    pass
                else: 
                    logger.info('successfully removed')    

def remove_oldinputs_db():
    """ removes Input-file data in the database where the upload-time is older than settings.KEEP_RESULTS_DAYS.
        The django based db access method models.InputFile.delete() is used.
    """
    todaysDate = datetime.date.today()
    no_of_days = datetime.timedelta(days = int(settings.KEEP_INPUTS_DAYS)) 
    reference_date = todaysDate - no_of_days
    file_candidates = InputFile.objects.filter(upload_time__lt=reference_date) ### __lt: less than
    count = len(file_candidates)
    if count > 0:
        logger.info(f" Cleanup database: delete {count} InputData entries from DB")     
    for inpfile in file_candidates:
        logger.info(f"input-id {inpfile.id}")
        inpfile.delete()



