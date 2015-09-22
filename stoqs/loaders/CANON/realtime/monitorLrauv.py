#!/usr/bin/env python
__author__    = 'Mike McCann, Danelle Cline'
__version__ = '$Revision: $'.split()[1]
__date__ = '$Date: $'.split()[1]
__copyright__ = '2011'
__license__   = 'GPL v3'
__contact__   = 'mccann at mbari.org'
__doc__ = '''

Monitor the dods web site for new realtime hotspot or sbdlog data from LRAUVs and use
DAPloaders.py to load new data into the stoqs database.

Mike McCann
MBARI 12 March 2014

@var __date__: Date of last svn commit
@undocumented: __doc__ parser
@status: production
@license: GPL
'''

import os
import sys
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../toNetCDF"))      # lrauvNc4ToNetcdf.py is in sister toNetCDF dir
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../"))           # settings.py is two dirs up


import DAPloaders
from CANON import CANONLoader
import logging
import lrauvNc4ToNetcdf
from datetime import datetime, timedelta
import time
import re
import pydap
import pytz
import Contour

from Contour import Contour
from thredds_crawler.crawl import Crawl
from coards import from_udunits
from stoqs.models import InstantPoint
from slacker import Slacker

from django.db.models import Max

# Set up global variables for logging output to STDOUT
logger = logging.getLogger('monitorLrauvLogger')
fh = logging.StreamHandler()
f = logging.Formatter("%(levelname)s %(asctime)sZ %(filename)s %(funcName)s():%(lineno)d %(message)s")
fh.setFormatter(f)
logger.addHandler(fh)
logger.setLevel(logging.DEBUG)

class NoNewHotspotData(Exception):
    pass

class NcFileMissing(Exception):
    def __init__(self, value):
        self.nc4FileUrl = value
    def __str__(self):
        return repr(self.nc4FileUrl)

class ServerError(Exception):
    pass

def abbreviate(parms):
    '''Return the shortened string that represents the list of parameters. This is used in both activity and file naming conventions'''
    dict = {'sea_water_temperature':'sst', 'sea_water_salinity':'salt', 'mass_concentration_of_chlorophyll_in_sea_water': 'chl'}
    abbrev = ''
    for p in parms:
        found = False
        for key,value in dict.iteritems():
            if p.find(key) != -1:
                abbrev = abbrev + '_' + value
                found = True
                break
        if not found:
            abbrev = abbrev + '_' + p[:2]

    return abbrev

def getNcStartEnd(urlNcDap, timeAxisName):
    '''Find the lines in the html with the .nc file, then open it and read the start/end times
    return url to the .nc  and start/end as datetime objects.
    '''
    logger.debug('open_url on urlNcDap = %s', urlNcDap)
    df = pydap.client.open_url(urlNcDap)
    try:
        timeAxisUnits = df[timeAxisName].units
    except KeyError as e:
        logger.warn(e)
        raise ServerError("Can't read %s time axis from %s" % (timeAxisName, urlNcDap))

    if timeAxisUnits == 'seconds since 1970-01-01T00:00:00Z' or timeAxisUnits == 'seconds since 1970/01/01 00:00:00Z':
        timeAxisUnits = 'seconds since 1970-01-01 00:00:00'    # coards is picky

    try:
        startDatetime = from_udunits(df[timeAxisName][0][0], timeAxisUnits)
        endDatetime = from_udunits(df[timeAxisName][-1][0], timeAxisUnits)
    except pydap.exceptions.ServerError as e:
        logger.warn(e)
        raise ServerError("Can't read start and end dates of %s from %s" % (timeAxisUnits, urlNcDap))
    except ValueError as e:
        logger.warn(e)
        raise ServerError("Can't read start and end dates of %s from %s" % (timeAxisUnits, urlNcDap)) 

    return startDatetime, endDatetime

def processDecimated(pw, url, lastDatetime, outDir, resample_freq, interp_freq, parm, interp_key, start, end, debug):
    '''
    Process decimated LRAUV data
    '''
    logger.debug('url = %s', url)

    if outDir.startswith('/tmp'):
        outFile_i = os.path.join(args.outDir, url.split('/')[-1].split('.')[0] + '_i.nc')
    else:
        outFile_i = os.path.join(args.outDir, '/'.join(url.split('/')[-2:]).split('.')[0] + '_i.nc')

    startDatetime, endDatetime = getNcStartEnd(url, 'depth_time')
    logger.debug('startDatetime, endDatetime = %s, %s', startDatetime, endDatetime)
    logger.debug('lastDatetime = %s', lastDatetime)

    if start is not None and startDatetime < start :
        raise ServerError('startDatetime = %s out of bounds with user-defined startDatetime = %s' % (startDatetime, start))

    if end is not None and endDatetime > end :
        raise ServerError('endDatetime = %s out of bounds with user-defined endDatetime = %s' % (endDatetime, end))

    url_i = None

    if endDatetime > lastDatetime:
        logger.debug('Calling pw.process with outFile_i = %s', outFile_i)
        try:
            if not debug:
                if len(interp_freq) == 0 or len(resample_freq) == 0 :
                    pw.process(url, outFile_i, parm, interp_key)
                else:
                    pw.processResample(url, outFile_i, parm, interp_freq, resample_freq)

        except TypeError as e:
            logger.warn('Problem reading data from %s', url)
            logger.warn('Assuming data are invalid and skipping')
        except IndexError as e:
            logger.warn('Problem interpolating data from %s', url)
        except KeyError as e:
            raise ServerError("Key error - can't read parameters from %s" % (url))
        except ValueError as e:
            raise ServerError("Value error - can't read parameters from %s" % (url))

        else:
            '''if outFile_i.startswith('/tmp'):
                # scp outFile_i to elvis, if unable to mount from elvis. Requires user to enter password.
                list = url.split('/') # get all strings delimited with /
                indx = list.index('LRAUV') # find first LRAUV string in the list
                dir = '/'.join(list[indx:-1]) # grab everything between LRAUV and the last string
                cmd = r'scp %s stoqsadm@elvis.shore.mbari.org:/mbari/%s' % (outFile_i, dir)
                logger.debug('%s', cmd)
                os.system(cmd)'''

            url_i = url.replace('.nc4', '_i.nc')
    else:
        logger.debug('endDatetime <= lastDatetime. Assume that data from %s have already been loaded', url)

    return url_i, startDatetime, endDatetime
    
def process_command_line():
        '''
        The argparse library is included in Python 2.7 and is an added package for STOQS.
        '''
        import argparse
        from argparse import RawTextHelpFormatter

        examples = 'Examples:' + '\n\n'
        examples += 'Run on test database:\n'
        examples += sys.argv[0] + " -d  'Test Daphne hotspot data' -o /mbari/LRAUV/daphne/realtime/hotspotlogs -u 'http://elvis.shore.mbari.org/thredds/catalog/LRAUV/daphne/realtime/hotspotlogs/*.shore.nc4' -b 'stoqs_canon_apr2014_t' -c 'CANON-ECOHAB - March 2014 Test'\n"
        parser = argparse.ArgumentParser(formatter_class=RawTextHelpFormatter,
                                         description='Read lRAUV data transferred over hotstpot and .nc file in compatible CF1-6 Discrete Sampling Geometry for for loading into STOQS',
                                         epilog=examples)
                                             
        '''parser.add_argument('-u', '--inUrl',action='store', help='url where hotspot/cell or other realtime processed data logs are. '
                                                                  'If interpolating, must map to the same location as -o directory', default='.',required=True)'''
        parser.add_argument('-u', '--inUrl',action='store', help='url where hotspot/cell or other realtime processed data logs are. '
                                                                 ' If interpolating, must map to the same location as -o directory',
                            default='http://elvis.shore.mbari.org/thredds/catalog/LRAUV/makai/realtime/sbdlogs/2015/201505/20150521T170042/.*shore.nc4$',required=False)
        '''parser.add_argument('-u', '--inUrl',action='store', help='url where hotspot/cell or other realtime processed data logs are. '
                                                                 ' If interpolating, must map to the same location as -o directory',
                            default='http://elvis.shore.mbari.org/thredds/catalog/LRAUV/daphne/realtime/cell-logs/.*Normal*.nc4$',required=False)'''

        #parser.add_argument('-b', '--database',action='store', help='name of database to load hotspot data to', default='default',required=True)
        parser.add_argument('-b', '--database',action='store', help='name of database to load hotspot data to', default='stoqs_lrauv',required=False)
        #parser.add_argument('-c', '--campaign',action='store', help='name of campaign', default='.',required=True)
        parser.add_argument('-c', '--campaign',action='store', help='name of campaign', default='April 2015 testing',required=False)
        parser.add_argument('-s', '--stride',action='store', help='amount to stride data before loading e.g. 10=every 10th point', default=1)
        #parser.add_argument('-o', '--outDir', action='store', help='output directory to store interpolated .nc file or contour output - must map to the same location as -u URL', default='', required=False)
        parser.add_argument('-o', '--outDir', action='store', help='output directory to store interpolated .nc file or log contour output '
                                                                   '- must map to the same location as -u URL', default='/tmp/TestMonitorLrauv', required=False)
        #parser.add_argument('-t', '--contourUrl', action='store', help='base url to store cross referenced contour plot resources', default='.',required=True)
        parser.add_argument('--contourUrl', action='store', help='base url to store cross referenced contour plot resources',
                            default='http://dods.mbari.org/opendap/data/lrauv/stoqs/',required=False)
        #parser.add_argument('-u', '--contourDir', action='store', help='output directory to store 24 hour contour output',
                            #default='/tmp/TestMonitorLrauv/',required=True)
        parser.add_argument('--iparm', action='store', help='parameter to interpolate against; must exist in the -p/--parms list',
                            default='bin_mean_mass_concentration_of_chlorophyll_in_sea_water',required=False)
        parser.add_argument('--contourDir', action='store', help='output directory to store 24 hour contour output',
                            default='/tmp/TestMonitorLrauv/',required=False)
        parser.add_argument('--productDir', action='store', help='output directory to store 24 hour contour output for catalog in ODSS',
                            default='/tmp/TestMonitorLrauv/',required=False)
        #parser.add_argument('-d', '--description', action='store', help='Brief description of experiment', default='.')
        parser.add_argument('-d', '--description', action='store', help='Brief description of experiment', default='Daphne Monterey data - April 2015')
        parser.add_argument('-i', '--interpolate', action='store_true', help='interpolate - must be used with --outDir option')
        parser.add_argument('--latest24hr', action='store_true', help='create the latest 24 hour plot')
        parser.add_argument('--autoscale', action='store_true', help='autoscale each plot to 1 and 99 percentile')
        #parser.add_argument('-a', '--append', action='store_false', help='Append data to existing Activity',required=False)
        parser.add_argument('-a', '--append', action='store_true', help='Append data to existing Activity',required=False)
        parser.add_argument('--post', action='store_true', help='Post message to slack about new data. Disable this during initial database load or when debugging',required=False)
        parser.add_argument('--debug', action='store_true', help='Useful for debugging plots - does not allow data loading',required=False, default=False)
        parser.add_argument('-f', '--interpFreq', action='store', help='Optional interpolation frequency string to specify time base for interpolating e.g. 500L=500 millisecs, 1S=1 second, 1Min=1 minute,H=1 hour,D=daily', default='')
        parser.add_argument('-r', '--resampleFreq', action='store', help='Optional resampling frequency string to specify how to resample interpolated results e.g. 2S=2 seconds, 5Min=5 minutes,H=1 hour,D=daily', default='')
        parser.add_argument('-p', '--parms', action='store', help='List of space separated parameters to load', nargs='*', default=
                                    ['bin_mean_sea_water_temperature', 'bin_mean_sea_water_salinity', 'sea_water_salinity', 'bin_mean_mass_concentration_of_chlorophyll_in_sea_water'])
        parser.add_argument('-g', '--plotgroup', action='store', help='List of space separated parameters to plot', nargs='*', default=
                                ['bin_mean_sea_water_temperature', 'bin_mean_sea_water_salinity', 'sea_water_salinity', 'bin_mean_mass_concentration_of_chlorophyll_in_sea_water'])

        parser.add_argument('-v', '--verbose', action='store_true', help='Turn on verbose output')
        parser.add_argument('--start', action='store', help='Start time in YYYYMMDDTHHMMSS format', default='20150518T000000', required=False)
        parser.add_argument('--end', action='store', help='Start time in YYYYMMDDTHHMMSS format', default=None, required=False)

        args = parser.parse_args()    
        return args

if __name__ == '__main__':
    colors = {  'tethys':       'fed976',
                'daphne':       'feb24c',
                'makai':        'feb2fc'}
  
    args = process_command_line() 

    if args.interpolate and len(args.outDir) < 1 :
        logger.error('Need to specify output directory with -o or --outDir option when interpolating')
        exit(-1)

    platformName = None

    # Url name for logs indicates what vehicle logs are being monitored; use this to determine the platform name
    d = re.match(r'.*tethys*',args.inUrl) 
    if d:
        platformName = 'tethys'
    d = re.match(r'.*daphne*',args.inUrl)
    if d:
        platformName = 'daphne'
    d = re.match(r'.*makai*',args.inUrl)
    if d:
        platformName = 'makai'

    if platformName is None:
        raise Exception('cannot find platformName from url %s' % args.inUrl)

    # Start back a week from now to load in old data
    lastDatetime = datetime.utcnow() - timedelta(days=7)

    # Unless start time defined, then start there
    if args.start is not None:
        dt = datetime.strptime(args.start, '%Y%m%dT%H%M%S')
        lastDatetime = dt
        start = dt
    else:
        start = None

    if args.end is not None:
        dt = datetime.strptime(args.end, '%Y%m%dT%H%M%S')
        end = dt
    else:
        end = None

    if args.post:
        token = os.environ['SLACKTOKEN']
        slack = Slacker(token)

    # Assume that the database has already been created with description and terrain information, so use minimal arguments in constructor
    cl = CANONLoader(args.database, args.campaign)
    cl.dbAlias = args.database
    cl.campaignName = args.campaign
   
    # Get directory list from sites
    s = args.inUrl.rsplit('/',1)
    files = s[1]
    url = s[0]
    logger.info("Crawling %s for %s files" % (url, files))
    c = Crawl(os.path.join(url, 'catalog.xml'), select=[files], debug=False)

    for d in c.datasets:
        logger.debug('Found %s' % d.id)
    
    urls = [s.get("url") for d in c.datasets for s in d.services if s.get("service").lower() == "opendap"]

    pw = lrauvNc4ToNetcdf.InterpolatorWriter()

    # If parameter names contains any group forward slash '/' delimiters
    # replace them with underscores. This is because pydap automatically renames slashes as underscores
    # and needs to reference the parameter correctly in the DAPloader
    parm_list = []
    plot_group = []
    parm_process = []
    coord = {}

    for p in args.parms:
        parm_fix = p.replace('/','_')
        #plot_group.append(parm_fix + '_i' + ',' + parm_fix)
        plot_group.append(parm_fix)
        #parm_list.append(parm_fix + '_i')
        parm_list.append(parm_fix)
        #coord[parm_fix + '_i'] = {'time': 'time', 'latitude': 'latitude', 'longitude': 'longitude', 'depth': 'depth'}
        coord[parm_fix] = {'time': p + '_time', 'latitude':  p +'_latitude', 'longitude':  p +'_longitude', 'depth':  p +'_depth'}
        parm_process.append(parm_fix)

        # Last parameter is the one to interpolate to - TODO: pass this in as a argument
        interp_key = parm_fix

    title = 'MBARI LRAUV Survey - ' + platformName

    # Look in time order - oldest to newest
    for url in sorted(urls):
        try:
            (url_i, startDatetime, endDatetime) = processDecimated(pw, url, lastDatetime, args.outDir,
                                                                   args.resampleFreq, args.interpFreq,
                                                                   parm_process, args.iparm, start, end, args.debug)
        except ServerError as e:
            logger.warn(e)
            continue
        except Exception as e:
            logger.warn(e)
            continue

        lastDatetime = endDatetime

        if url_i:
            logger.info("Received new %s data ending at %s in %s" % (platformName, endDatetime, url_i))
            # Use Hyrax server to workaround the caching that TDS does
            url_src = url_i.replace('http://elvis.shore.mbari.org/thredds/dodsC/LRAUV', 'http://dods.mbari.org/opendap/data/lrauv')

            logger.info("Received new %s file ending at %s in %s" % (platformName, lastDatetime, url_src))
            aName = url_src.split('/')[-2] + '_' + url_src.split('/')[-1].split('.')[0]
            dataStartDatetime = None

            if args.append:
                # Return datetime of last timevalue - if data are loaded from multiple activities return the earliest last datetime value
                dataStartDatetime = InstantPoint.objects.using(args.database).filter(activity__name=aName).aggregate(Max('timevalue'))['timevalue__max']

            try:
                if not args.debug:
                    logger.info("Instantiating Lrauv_Loader for url = %s", url_src)
                    lrauvLoad = DAPloaders.runLrauvLoader(cName = args.campaign,
                                                      cDesc = None,
                                                      aName = aName,
                                                      aTypeName = 'LRAUV mission',
                                                      pName = platformName,
                                                      pTypeName = 'auv',
                                                      pColor = colors[platformName],
                                                      url = url_src,
                                                      parmList = parm_list,
                                                      dbAlias = args.database,
                                                      stride = int(args.stride),
                                                      startDatetime = startDatetime,
                                                      dataStartDatetime = dataStartDatetime,
                                                      endDatetime = endDatetime,
                                                      contourUrl = args.contourUrl,
                                                      auxCoords = coord)

                endDatetimeUTC = pytz.utc.localize(endDatetime)
                endDatetimeLocal = endDatetimeUTC.astimezone(pytz.timezone('America/Los_Angeles'))
                startDatetimeUTC = pytz.utc.localize(startDatetime)
                startDatetimeLocal = startDatetimeUTC.astimezone(pytz.timezone('America/Los_Angeles'))

                # format contour output file name replacing file extension with .png
                if args.outDir.startswith('/tmp'):
                    outFile = os.path.join(args.outDir, url_src.split('/')[-1].split('.')[0] + '.png')
                else:
                    outFile = os.path.join(args.outDir, '/'.join(url_src.split('/')[-2:]).split('.')[0]  + '.png')

                logger.debug('out file %s', outFile)

                c = Contour(startDatetimeUTC, endDatetimeUTC, args.database, [platformName], plot_group, title, outFile, False, args.autoscale)
                c.run()

                # Replace netCDF file with png extension and that is the URL of the log
                logUrl = re.sub('\.nc$','.png', url_src)

                '''if outFile.startswith('/tmp'):
                    # scp outFile_i to elvis, if unable to mount from elvis. Requires user to enter password.
                    list = url.split('/') # get all strings delimited with /
                    indx = list.index('LRAUV') # find first LRAUV string in the list
                    dir = '/'.join(list[indx:-1]) # grab everything between LRAUV and the last string
                    cmd = r'scp %s stoqsadm@elvis.shore.mbari.org:/mbari/%s' % (outFile, dir)
                    logger.debug('%s', cmd)
                    os.system(cmd)'''

                # Round the UTC time to the local time and do the query for the 24 hour period the log file falls into
                startDatetime = startDatetimeUTC
                startDateTimeLocal = startDatetime.astimezone(pytz.timezone('America/Los_Angeles'))
                startDateTimeLocal = startDateTimeLocal.replace(hour=0,minute=0,second=0,microsecond=0)
                startDateTimeUTC24hr = startDateTimeLocal.astimezone(pytz.utc)

                endDatetime = startDateTimeLocal
                endDateTimeLocal = endDatetime.replace(hour=23,minute=59,second=0,microsecond=0)
                endDateTimeUTC24hr = endDateTimeLocal.astimezone(pytz.utc)

                outFile = args.contourDir + '/' + platformName  + '_log_' + startDateTimeUTC24hr.strftime('%Y%m%dT%H%M%S') + '_' + endDateTimeUTC24hr.strftime('%Y%m%dT%H%M%S') + '.png'
                url = args.contourUrl + platformName  + '_log_' + startDateTimeUTC24hr.strftime('%Y%m%dT%H%M%S') + '_' + endDateTimeUTC24hr.strftime('%Y%m%dT%H%M%S') + '.png'

                logger.debug('out file %s url: %s ', outFile, url)
                c = Contour(startDateTimeUTC24hr, endDateTimeUTC24hr, args.database, [platformName], args.plotgroup, title, outFile, False, args.autoscale)
                c.run()

                if outFile.startswith('/tmp'):
                    # scp outFile_i to elvis, if unable to mount from elvis. Requires user to enter password.
                    '''list = args.contourUrl.split('/') # get all strings delimited with /
                    indx = list.index('lrauv') # find first LRAUV string in the list
                    dir = '/'.join(list[indx+1:-1]) # grab everything after LRAUV and the last string
                    cmd = r'scp %s stoqsadm@elvis.shore.mbari.org:/mbari/LRAUV/%s' % (outFile, dir)
                    logger.debug('%s', cmd)
                    os.system(cmd)'''

                if args.post:
                    message = 'LRAUV log data processed through STOQs workflow. Log <%s|%s plot> ' % (logUrl, aName)
                    slack.chat.post_message("#lrauvs", message)


            except DAPloaders.NoValidData:
                logger.info("No measurements in this log set. Activity was not created as there was nothing to load.")
 
            except pydap.exceptions.ServerError as e:
                logger.warn(e)

            except DAPloaders.ParameterNotFound as e:
                logger.warn(e)

            except DAPloaders.InvalidSliceRequest as e:
                logger.warn(e)

            except Exception as e:
                logger.warn(e)
                continue


    # update last 24 hr plot when requested
    if args.latest24hr:
        try:
            # Plot the last 24 hours
            nowStart = datetime.utcnow() - timedelta(hours=24)
            nowEnd = datetime.utcnow()
            nowStartDateTimeUTC24hr = pytz.utc.localize(nowStart)
            nowEndDateTimeUTC24hr = pytz.utc.localize(nowEnd)

            outFileLatest = args.contourDir + '/' + platformName  + '_24h_latest.png'
            outFileLatestProduct = args.productDir + '/' + platformName  + '_log_last24hr.png'

            c = Contour(nowStartDateTimeUTC24hr, nowEndDateTimeUTC24hr, args.database, [platformName], args.plotgroup, title, outFileLatest, False, args.autoscale)
            c.run()

            if outFileLatest.startswith('/tmp'):
                # scp outFile_i to elvis, if unable to mount from elvis. Requires user to enter password.
                '''list = args.contourUrl.split('/') # get all strings delimited with /
                indx = list.index('lrauv') # find first LRAUV string in the list
                dir = '/'.join(list[indx+1:-1]) # grab everything after LRAUV and the last string
                cmd = r'scp %s stoqsadm@elvis.shore.mbari.org:/mbari/LRAUV/%s' % (outFileLatest, args.productDir)
                logger.debug('%s', cmd)
                os.system(cmd)'''
            else:
                # copy to the atlas share that will get cataloged in ODSS
                cmd = r'cp %s %s' %(outFileLatest, outFileLatestProduct)
                logger.debug('%s', cmd)
                os.system(cmd)

            '''if args.post:
                    urlLatest = args.productDir + platformName  +  '_24h_latest.png'
                    message = 'LRAUV log data processed through STOQs workflow. last 24-hr <%s|%s plot> ' % (urlLatest, aName)
                    slack.chat.post_message("#lrauvs", message)'''

        except Exception as e:
            logger.warn(e)


    logger.info('done')