#!/usr/bin/env python
__author__    = 'Mike McCann'
__copyright__ = '2013'
__license__   = 'GPL v3'
__contact__   = 'mccann at mbari.org'

__doc__ = '''

Master loader for all March 2013 CANON-ECOHAB activities.  

The default is to load data with a stride of 100 into a database named stoqs_march2013_s100.

Execute with "./loadCANON_march2013 1 stoqs_march2013" to load full resolution data.

Mike McCann
MBARI 13 March 2013

@var __date__: Date of last svn commit
@undocumented: __doc__ parser
@status: production
@license: GPL
'''

import os
import sys
import datetime
os.environ['DJANGO_SETTINGS_MODULE']='settings'
project_dir = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../"))  # settings.py is one dir up

from CANON import CANONLoader

try:
    stride = int(sys.argv[1])
except IndexError:
    stride = 100
except ValueError:
    # Not an integer
    stride = 'optimal'

try:
    dbAlias = sys.argv[2]
except IndexError:
    dbAlias = 'stoqs_march2013_s100'


# ------------------------------------------------------------------------------------
# Data loads for all the activities, LRAUV have real-time files before full-resolution
# ------------------------------------------------------------------------------------
campaignName = 'CANON-ECOHAB - March 2013'
if stride != 1:
    try:
        campaignName = campaignName + ' with stride=%d' % stride
    except TypeError:
        # Not an integer
        campaignName = campaignName + ' with appropriate strides'

cl = CANONLoader(dbAlias, campaignName)

# Aboard the Carson use zuma
##cl.tdsBase = 'http://zuma.rc.mbari.org/thredds/'       
cl.tdsBase = 'http://odss.mbari.org/thredds/'       # Use this on shore
cl.dodsBase = cl.tdsBase + 'dodsC/'       

# 2-second decimated dorado data
cl.dorado_base = cl.dodsBase + 'CANON_march2013/dorado/'
cl.dorado_files = [ 
                    'Dorado389_2013_074_02_074_02_decim.nc',
                    'Dorado389_2013_075_05_075_06_decim.nc',
                    'Dorado389_2013_076_01_076_02_decim.nc',
                    'Dorado389_2013_079_04_079_04_decim.nc',
                    'Dorado389_2013_080_02_080_02_decim.nc',
                    'Dorado389_2013_081_05_081_05_decim.nc',
                    'Dorado389_2013_081_06_081_06_decim.nc',
                  ]

# Realtime telemetered (_r_) daphne data - insert '_r_' to not load the files
##cl.daphne_base = 'http://aosn.mbari.org/lrauvtds/dodsC/lrauv/daphne/2012/'
cl.daphne_r_base = cl.dodsBase + 'CANON_march2013/lrauv/daphne/realtime/sbdlogs/2013/201303/'
cl.daphne_r_files = [ 
                    'shore_201303132226_201303140449.nc',
                    'shore_201303140708_201303140729.nc',
                    'shore_201303140729_201303141609.nc',
                    'shore_201303141631_201303151448.nc',
                    'shore_201303141631_201303181540.nc',
                  ]
cl.daphne_r_parms = [ 'sea_water_temperature', 'mass_concentration_of_chlorophyll_in_sea_water']

# Postrecovery full-resolution (_d_) daphne data - insert '_d_' for delayed-mode to not load the data
cl.daphne_base = 'http://dods.mbari.org/opendap/hyrax/data/lrauv/daphne/missionlogs/2013/'
cl.daphne_files = [ 
                    '20130313_20130318/20130313T195025/201303131950_201303132226.nc',
                    '20130313_20130318/20130313T222616/201303132226_201303140705.nc',
                    '20130313_20130318/20130314T070622/201303140706_201303140729.nc',
                    '20130313_20130318/20130314T072813/201303140728_201303141601.nc',
                    '20130313_20130318/20130314T072813/201303141601_201303141629.nc',
                    '20130313_20130318/20130314T162843/201303141628_201303141924.nc',
                    '20130313_20130318/20130314T162843/201303141901_201303150303.nc',
                    '20130313_20130318/20130314T162843/201303150303_201303151019.nc',
                    '20130313_20130318/20130314T162843/201303151019_201303151821.nc',
                    '20130313_20130318/20130314T162843/201303151821_201303151901.nc',
                    '20130313_20130318/20130314T162843/201303151901_201303160253.nc',
                    '20130313_20130318/20130314T162843/201303160253_201303161024.nc',
                    '20130313_20130318/20130314T162843/201303161024_201303161826.nc',
                    '20130313_20130318/20130314T162843/201303161826_201303161900.nc',
                    '20130313_20130318/20130314T162843/201303161900_201303162301.nc',
                    '20130313_20130318/20130314T162843/201303162301_201303170637.nc',
                    '20130313_20130318/20130314T162843/201303170637_201303171444.nc',
                    '20130313_20130318/20130314T162843/201303171444_201303171701.nc',
                    '20130313_20130318/20130314T162843/201303171701_201303180033.nc',
                    '20130313_20130318/20130314T162843/201303180033_201303180835.nc',
                    '20130313_20130318/20130314T162843/201303180835_201303180904.nc',
                    '20130313_20130318/20130314T162843/201303180904_201303181637.nc',
                    '20130313_20130318/20130314T162843/201303181637_201303181649.nc',
                    '20130313_20130318/20130318T165540/201303181655_201303182153.nc',

                  ]
cl.daphne_parms = [ 'sea_water_temperature', 'sea_water_salinity', 'sea_water_density', 'volume_scattering_470_nm', 
                    'volume_scattering_650_nm', 'mass_concentration_of_oxygen_in_sea_water', 'mole_concentration_of_nitrate_in_sea_water',
                    'mass_concentration_of_chlorophyll_in_sea_water']

# Realtime telemetered (_r_) tethys data - insert '_r_' to not load the files
cl.tethys_r_base = cl.dodsBase + 'CANON_march2013/lrauv/tethys/realtime/sbdlogs/2013/201303/'
cl.tethys_r_files = [ 
                    'shore_201303140812_201303141247.nc',
                    'shore_201303141252_201303141329.nc',
                    'shore_201303141331_201303150644.nc',
                    'shore_201303150645_201303151308.nc',
                    'shore_201303151312_201303151339.nc',
                    'shore_201303151333_201303151334.nc',
                    'shore_201303151337_201303151503.nc',
                    'shore_201303151504_201303151706.nc',
                    'shore_201303151714_201303151730.nc',
                    'shore_201303151728_201303151747.nc',
                    'shore_201303151748_201303151947.nc',
                    'shore_201303151950_201303152001.nc',
                    'shore_201303152003_201303152011.nc',
                    'shore_201303152013_201303152026.nc',
                    'shore_201303152027_201303160953.nc',
                    'shore_201303160958_201303161025.nc',
                    'shore_201303161027_201303161039.nc',
                    'shore_201303161041_201303170254.nc',
                    'shore_201303170334_201303170607.nc',
                    'shore_201303170616_201303170638.nc',
                    'shore_201303170641_201303170646.nc',
                    'shore_201303170647_201303171828.nc',
                    'shore_201303171835_201303171849.nc',
                    'shore_201303171851_201303171856.nc',
                    'shore_201303171857_201303172034.nc',
                    'shore_201303172042_201303172051.nc',
                    'shore_201303172055_201303172058.nc',
                    'shore_201303172059_201303180702.nc',
                    'shore_201303180717_201303180736.nc',
                    'shore_201303180733_201303180742.nc',
                    'shore_201303180743_201303181632.nc',       # Incomplete list of shore files
                                                                # Put effort into loading full-resolution data
                  ]
cl.tethys_r_parms = [ 'sea_water_temperature', 'mass_concentration_of_chlorophyll_in_sea_water', 'mole_concentration_of_nitrate_in_sea_water',
                    'platform_x_velocity_current', 'platform_y_velocity_current', 'platform_z_velocity_current']

# Postrecovery full-resolution tethys data - insert '_d_' for delayed-mode to not load the data
cl.tethys_base = 'http://dods.mbari.org/opendap/hyrax/data/lrauv/tethys/missionlogs/2013/'
cl.tethys_files = [ 
                    '20130313_20130320/20130313T203723/201303132037_201303132240.nc',
                    '20130313_20130320/20130313T224020/201303132240_201303140239.nc',
                    '20130313_20130320/20130314T023827/201303140238_201303140715.nc',
                    '20130313_20130320/20130314T071458/201303140715_201303140731.nc',
                    '20130313_20130320/20130314T073047/201303140731_201303140803.nc',
                    '20130313_20130320/20130314T080454/201303140805_201303140811.nc',
                    '20130313_20130320/20130314T081138/201303140811_201303141248.nc',
                    '20130313_20130320/20130314T125102/201303141251_201303141329.nc',
                    '20130313_20130320/20130314T133105/201303141331_201303141602.nc',
                    '20130313_20130320/20130314T133105/201303141602_201303142309.nc',
                    '20130313_20130320/20130314T133105/201303142309_201303150644.nc',
                    '20130313_20130320/20130315T064246/201303150643_201303150909.nc',
                    '20130313_20130320/20130315T064246/201303150802_201303151102.nc',
                    '20130313_20130320/20130315T064246/201303151102_201303151308.nc',
                    '20130313_20130320/20130315T131039/201303151310_201303151331.nc',
                    '20130313_20130320/20130315T133305/201303151333_201303151335.nc',
                    '20130313_20130320/20130315T133635/201303151336_201303151503.nc',
                    '20130313_20130320/20130315T150400/201303151504_201303151706.nc',
                    '20130313_20130320/20130315T150400/201303151601_201303151706.nc',
                    '20130313_20130320/20130315T170914/201303151709_201303151725.nc',
                    '20130313_20130320/20130315T172729/201303151727_201303151747.nc',
                    '20130313_20130320/20130315T174744/201303151747_201303151947.nc',
                    '20130313_20130320/20130315T195016/201303151950_201303152002.nc',
                    '20130313_20130320/20130315T200217/201303152002_201303152011.nc',
                    '20130313_20130320/20130315T201305/201303152013_201303152027.nc',
                    '20130313_20130320/20130315T202717/201303152027_201303160254.nc',
                    '20130313_20130320/20130315T202717/201303152201_201303160004.nc',
                    '20130313_20130320/20130315T202717/201303160004_201303160651.nc',
                    '20130313_20130320/20130315T202717/201303160651_201303160953.nc',
                    '20130313_20130320/20130316T095712/201303160957_201303161025.nc',
                    '20130313_20130320/20130316T102632/201303161026_201303161040.nc',
                    '20130313_20130320/20130316T104017/201303161040_201303161529.nc',
                    '20130313_20130320/20130316T104017/201303161302_201303162011.nc',
                    '20130313_20130320/20130316T104017/201303162011_201303170333.nc',
                    '20130313_20130320/20130317T033239/201303170332_201303170608.nc',
                    '20130313_20130320/20130317T033239/201303170602_201303170608.nc',
                    '20130313_20130320/20130317T061040/201303170610_201303170639.nc',
                    '20130313_20130320/20130317T064112/201303170641_201303170646.nc',
                    '20130313_20130320/20130317T064639/201303170646_201303170944.nc',
                    '20130313_20130320/20130317T064639/201303170802_201303171511.nc',
                    '20130313_20130320/20130317T064639/201303171511_201303171828.nc',
                    '20130313_20130320/20130317T183135/201303171831_201303171849.nc',
                    '20130313_20130320/20130317T185106/201303171851_201303171856.nc',
                    '20130313_20130320/20130317T185723/201303171857_201303172006.nc',
                    '20130313_20130320/20130317T185723/201303172006_201303172034.nc',
                    '20130313_20130320/20130317T203717/201303172037_201303172051.nc',
                    '20130313_20130320/20130317T205336/201303172053_201303172058.nc',
                    '20130313_20130320/20130317T205906/201303172059_201303172244.nc',
                    '20130313_20130320/20130317T205906/201303172202_201303180512.nc',
                    '20130313_20130320/20130317T205906/201303180512_201303180702.nc',
                    '20130313_20130320/20130318T070527/201303180705_201303180731.nc',
                    '20130313_20130320/20130318T073303/201303180733_201303180742.nc',
                    '20130313_20130320/20130318T074256/201303180743_201303180903.nc',
                    '20130313_20130320/20130318T074256/201303180903_201303181606.nc',
                    '20130313_20130320/20130318T074256/201303181606_201303182352.nc',
                    '20130313_20130320/20130318T074256/201303182352_201303190101.nc',
                    '20130313_20130320/20130318T074256/201303190101_201303190235.nc',
                    '20130313_20130320/20130319T023834/201303190238_201303190257.nc',
                    '20130313_20130320/20130319T025944/201303190300_201303190302.nc',
                    '20130313_20130320/20130319T030324/201303190303_201303190721.nc',
                    '20130313_20130320/20130319T030324/201303190703_201303190817.nc',
                    '20130313_20130320/20130319T081955/201303190820_201303190845.nc',
                    '20130313_20130320/20130319T084718/201303190847_201303190849.nc',
                    '20130313_20130320/20130319T085014/201303190850_201303192307.nc',
                    '20130313_20130320/20130319T085014/201303191101_201303191804.nc',
                    '20130313_20130320/20130319T085014/201303191804_201303192307.nc',
                    '20130313_20130320/20130319T231047/201303192311_201303192333.nc',
                    '20130313_20130320/20130319T233504/201303192335_201303200004.nc',
                    '20130313_20130320/20130320T000452/201303200005_201303200056.nc',
                    '20130313_20130320/20130320T005923/201303200059_201303200132.nc',
                    '20130313_20130320/20130320T013358/201303200134_201303200136.nc',
                    '20130313_20130320/20130320T014500/201303200145_201303200203.nc',
                    '20130313_20130320/20130320T014500/201303200145_201303200228.nc',
                    '20130313_20130320/20130320T014500/201303200203_201303200916.nc',
                    '20130313_20130320/20130320T091648/201303200918_201303201726.nc',
                    '20130313_20130320/20130320T172551/201303201726_201303201854.nc',

                  ]

cl.tethys_parms = [ 'sea_water_temperature', 'sea_water_salinity', 'sea_water_density', 'volume_scattering_470_nm', 
                    'volume_scattering_650_nm', 'mass_concentration_of_oxygen_in_sea_water', 'mole_concentration_of_nitrate_in_sea_water',
                    'mass_concentration_of_chlorophyll_in_sea_water']

# Webb gliders
cl.hehape_base = cl.dodsBase + 'CANON_march2013/usc_glider/HeHaPe/processed/'
cl.hehape_files = [
                        'OS_Glider_HeHaPe_20130305_TS.nc',
                        'OS_Glider_HeHaPe_20130310_TS.nc',
                   ]
cl.hehape_parms = [ 'TEMP', 'PSAL', 'BB532', 'CDOM', 'CHLA', 'DENS' ]

cl.rusalka_base = cl.dodsBase + 'CANON_march2013/usc_glider/Rusalka/processed/'
cl.rusalka_files = [
                        'OS_Glider_Rusalka_20130301_TS.nc',
                   ]
cl.rusalka_parms = [ 'TEMP', 'PSAL', 'BB532', 'CDOM', 'CHLA', 'DENS' ]

# Spray glider - for just the duration of the campaign
cl.l_662_base = 'http://www.cencoos.org/thredds/dodsC/glider/'
cl.l_662_files = ['OS_Glider_L_662_20120816_TS.nc']
cl.l_662_parms = ['TEMP', 'PSAL', 'FLU2']
cl.l_662_startDatetime = datetime.datetime(2012, 9, 10)
cl.l_662_endDatetime = datetime.datetime(2012, 9, 20)


# MBARI ESPs Mack and Bruce
cl.espmack_base = cl.dodsBase + 'CANON_march2013/esp/instances/Mack/data/processed/'
cl.espmack_files = [ 
                        'ctd.nc',
                      ]
cl.espmack_parms = [ 'TEMP', 'PSAL', 'chl', 'chlini', 'no3' ]

# Rachel Carson Underway CTD
cl.rcuctd_base = cl.dodsBase + 'CANON_march2013/carson/uctd/'
cl.rcuctd_files = [ 
                        '07413plm01.nc', '07513plm02.nc', '07613plm03.nc', '07913plm04.nc',
                        '08013plm05.nc', '08113plm06.nc',
                      ]
cl.rcuctd_parms = [ 'TEMP', 'PSAL', 'xmiss', 'wetstar' ]

# Rachel Carson Profile CTD
cl.pctdDir = 'CANON_march2013/carson/pctd/'
cl.rcpctd_base = cl.dodsBase + cl.pctdDir
cl.rcpctd_files = [ 
                    '07413c01.nc', '07413c02.nc', '07413c03.nc', '07413c04.nc', '07413c05.nc', '07413c06.nc', '07413c07.nc',
                    '07413c08.nc', '07413c09.nc', '07413c10.nc', '07413c11.nc', '07513c12.nc', '07513c13.nc', '07513c14.nc',
                    '07513c15.nc', '07513c16.nc', '07513c17.nc', '07513c18.nc', '07513c19.nc', '07613c20.nc', '07613c21.nc',
                    '07613c22.nc', '07613c23.nc', '07613c24.nc', '07613c25.nc', '07613c26.nc', '07913c27.nc', '07913c28.nc',
                    '07913c29.nc', '07913c30.nc', '07913c31.nc', '08013c32.nc', '08013c33.nc', '08013c34.nc', '08013c35.nc',
                    '08013c36.nc', '08113c37.nc', '08113c38.nc', '08113c39.nc', '08113c40.nc', '08113c41.nc', '08113c42.nc',
                    '08113c43.nc',
                      ]
cl.rcpctd_parms = [ 'TEMP', 'PSAL', 'xmiss', 'ecofl', 'oxygen' ]

# Spray glider - for just the duration of the campaign
##cl.l_662_base = 'http://www.cencoos.org/thredds/dodsC/glider/'
##cl.l_662_files = ['OS_Glider_L_662_20120816_TS.nc']
##cl.l_662_parms = ['TEMP', 'PSAL', 'FLU2']
##cl.l_662_startDatetime = datetime.datetime(2012, 9, 1)
##cl.l_662_endDatetime = datetime.datetime(2012, 9, 21)


# Load the data with the appropriate stride
if stride == 'optimal':
    cl.loadDorado(stride=2)
    cl.loadDaphne(stride=10)
    cl.loadTethys(stride=10)
    ##cl.loadESPmack()
    ##cl.loadESPbruce()
    cl.loadRCuctd(stride=1)
    cl.loadRCpctd(stride=1)
    ##cl.loadHeHaPe(stride=10)        # As of 3/18/2013 - Bad Lat & Lon
    ##cl.loadRusalka(stride=10)     # As of 3/18/2013 - no good data in file http://zuma.rc.mbari.org/thredds/dodsC/CANON_march2013/usc_glider/Rusalka/processed/OS_Glider_Rusalka_20130301_TS.nc.html
    ##cl.loadYellowfin()
else:
    cl.loadDorado()
    cl.loadDaphne()
    cl.loadTethys()
    ##cl.loadESPmack()
    ##cl.loadESPbruce()
    cl.loadRCuctd()
    cl.loadRCpctd()
    ##cl.loadHeHaPe()
    ##cl.loadRusalka()
    ##cl.loadYellowfin()

