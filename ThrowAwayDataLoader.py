import DatabaseObjects
import InversionConfiguration
import Fault
from sqlalchemy import exists, and_
from OldVersionValidation import CompareWrappers
import dist_filt

inversion_runs = [
    {
        'sites_file': './ThrowAwayData/CAS_offset.d',
        'faults_file': './ThrowAwayData/CAS_faults.d',
        'sites': None,
        'faults': None,
        'filters': None,
        'model': 'Cascadia-20x10',
        'label': 'Refactor Version',
        'tag': 'current',
        'minimum_offset': 0.001,  # inverter config/validator/readonceconfig
        'convergence': 45.,  # read once config
        'eq_pause': 120.,
        'eq_threshold': 1.,
        'strike_slip': False,
        'mes_wait': 2,
        'max_offset': 100,
        'offset': False,
        'min_r': 0.0001,
        'float_equality': 1e-9,
        'inverter_configuration': {
            'strike_slip': None,
            'short_smoothing': True,
            'smoothing': True,
            'corner_fix': False,
            'offsets_per_site': 3,
            'subfault_len': 60.,
            'subfault_wid': 30.,
            'offset': None,
            'sub_inputs': None,
            'smooth_mat': None,
            'mask': None
        }
    },
    {
        'sites_file': './ThrowAwayData/SA_offset.d',
        'faults_file': './ThrowAwayData/SA_faults.d',
        'sites': None,
        'faults': None,
        'filters': None,
        'model': 'SanAndreas-20x4',
        'label': 'Refactor Version',
        'tag': 'current',
        'minimum_offset': 0.001,  # inverter config/validator/readonceconfig
        'convergence': 320.,  # read once config
        'eq_pause': 10.,
        'eq_threshold': 0.01,
        'strike_slip': False,
        'mes_wait': 2,
        'max_offset': 4000,
        'offset': False,
        'min_r': 0.0001,
        'float_equality': 1e-9,
        'inverter_configuration': {
            'strike_slip': None,
            'short_smoothing': True,
            'smoothing': True,
            'corner_fix': False,
            'offsets_per_site': 3,
            'subfault_len': 60.,
            'subfault_wid': 30.,
            'offset': None,
            'sub_inputs': None,
            'smooth_mat': None,
            'mask': None
        }
    },
    {
        'sites_file': './ThrowAwayData/MAT_offset.d',
        'faults_file': './ThrowAwayData/MAT_faults.d',
        'sites': None,
        'faults': None,
        'filters': None,
        'model': 'MAT-57x4',
        'label': 'Refactor Version',
        'tag': 'current',
        'minimum_offset': 0.001,  # inverter config/validator/readonceconfig
        'convergence': 320.,  # read once config
        'eq_pause': 120.,
        'eq_threshold': 1.,
        'strike_slip': False,
        'mes_wait': 2,
        'max_offset': 100,
        'offset': False,
        'min_r': 0.0001,
        'float_equality': 1e-9,
        'inverter_configuration': {
            'strike_slip': None,
            'short_smoothing': True,
            'smoothing': True,
            'corner_fix': False,
            'offsets_per_site': 3,
            'subfault_len': 60.,
            'subfault_wid': 30.,
            'offset': None,
            'sub_inputs': None,
            'smooth_mat': None,
            'mask': None
        }
    },
    {
        'sites_file': './ThrowAwayData/NAZ_offset.d',
        'faults_file': './ThrowAwayData/NAZ_faults.d',
        'sites': None,
        'faults': None,
        'filters': None,
        'model': 'Nazca-40x4',
        'label': 'Refactor Version',
        'tag': 'current',
        'minimum_offset': 0.001,  # inverter config/validator/readonceconfig
        'convergence': 320.,  # read once config
        'eq_pause': 120.,
        'eq_threshold': .1,
        'strike_slip': False,
        'mes_wait': 2,
        'max_offset': 100,
        'offset': False,
        'min_r': 0.0001,
        'float_equality': 1e-9,
        'inverter_configuration': {
            'strike_slip': None,
            'short_smoothing': True,
            'smoothing': True,
            'corner_fix': False,
            'offsets_per_site': 3,
            'subfault_len': 60.,
            'subfault_wid': 30.,
            'offset': None,
            'sub_inputs': None,
            'smooth_mat': None,
            'mask': None
        }
    }
]


def populate_sites():
    for run in inversion_runs:
        with open(run['sites_file'], "r") as f:
            sites = f.readlines()
            for site in sites:
                name, lat, lon, ele, _ = site.split()
                try:
                    DatabaseObjects.Site.create(name=name, lat=lat, lon=lon, ele=ele)
                except DatabaseObjects.DataError:
                    pass



def populate_inversions():
    for run in inversion_runs:
        with open(run['faults_file']) as file:
            fault_data = [x.split() for x in file.readlines() if x[0] != '#']

        faults_dict = {
            'length': int(fault_data[0][0]),
            'width': int(fault_data[0][1]),
            'subfault_list': [[float(x) for x in fault_data_line] for fault_data_line in fault_data[1:]]
        }

        kal = DatabaseObjects.KalmanConfiguration.create(max_offset=run['max_offset'], min_r=run['min_r'],
                                                         eq_pause=run['eq_pause'], eq_threshold=run['eq_threshold'],
                                                         mes_wait=run['mes_wait'],
                                                         name="{} {}".format(run['model'], 'Kalman Config'))

        fault_object_list = []
        for subfault in faults_dict['subfault_list']:
            fault_object_list.append(Fault.Fault(subfault[0], subfault[1], subfault[2], subfault[3], subfault[4],
                                                 subfault[5], subfault[6], subfault[7]))
        faults = Fault.SolutionFaults(faults_dict['length'], faults_dict['width'], fault_object_list)
        conf = DatabaseObjects.\
            InversionConfiguration(faults=faults, model=run['model'],
                                   label=run['label'], tag=run['tag'])
        conf.smoothing = run['inverter_configuration']['smoothing']
        conf.corner_fix = run['inverter_configuration']['corner_fix']
        conf.short_smoothing = run['inverter_configuration']['short_smoothing']
        conf.convergence = run['convergence']
        conf.min_offset = run['minimum_offset']
        conf.delay_timespan = 15
        conf.kalman_configuration = kal
        print (vars(conf))
        DatabaseObjects.InversionConfiguration.create(obj=conf)

def generate_offsets():
    session = DatabaseObjects.get_db_session()
    inversions = DatabaseObjects.InversionConfiguration.get_all()

    for inversion in inversions:
        for site in DatabaseObjects.Site.get_sites_missing_offset(inversion):
            max_mag = 0
            for fault in inversion.faults.fault_list:
                slip = 1  # from example usage, not sure what this means
                rake = 180  # from example usage, not sure why real rake value isn't used

                mag = CompareWrappers.mangle\
                    (fault.lat, fault.lon, fault.depth, fault.strike, fault.dip,
                     rake, fault.length, fault.width, slip, site.lat, site.lon)

                max_mag = max(mag, max_mag)
            print("{} {} {}".format(site.name, inversion.model, max_mag))
            DatabaseObjects.SiteInversionAssociation.create(inversion=inversion, site=site, offset=max_mag)


def validate_offsets():
    for run in inversion_runs:
        db_run = DatabaseObjects.InversionConfiguration.get_by_field(DatabaseObjects.InversionConfiguration.model,
                                                                     run['model'])[0]
        print (db_run.model)
        with open(run['sites_file'], "r") as f:
            sites = f.readlines()
            for site in sites:
                name, lat, lon, ele, mag = site.split()
                #if name == 'ALBH':
                mag = float(mag)
                site = DatabaseObjects.Site.get_by_field(DatabaseObjects.Site.name, name)[0]
                db_mag = DatabaseObjects.SiteInversionAssociation.\
                    get_offset_by_site_and_inversion(site, db_run)
                diff = mag - db_mag
                if abs(diff) > 0.0005:
                    max_mag = 0
                    max_mag2 = 0
                    for fault in db_run.faults.fault_list:
                        slip = 1  # from example usage, not sure what this means
                        rake = 180  # from example usage, not sure why real rake value isn't used

                        mag = dist_filt.adp \
                            (fault.lat, fault.lon, fault.depth, fault.strike, fault.dip,
                             rake, fault.length, fault.width, slip, site.lat, site.lon)
                        mag2 = CompareWrappers.mangle(fault.lat, fault.lon, fault.depth, fault.strike, fault.dip,
                             rake, fault.length, fault.width, slip, site.lat, site.lon)

                        max_mag = max(mag, max_mag)
                        max_mag2 = max(mag2, max_mag2)
                    if abs(max_mag - max_mag2) > 0.0005:
                        print("NOT OK: {} {} {} {} {}".format(site.name, mag, db_mag, max_mag, max_mag2))
                    else:
                        print("OK: {} {} {} {} {}".format(site.name, mag, db_mag, max_mag, max_mag2))

def create_inversion_configurations():
    db_runs = DatabaseObjects.InversionConfiguration.get_all()
    for db_run in db_runs:
        sites_join = DatabaseObjects.Site.get_sites_by_offset_and_inversion(db_run, db_run.min_offset)
        config = InversionConfiguration.inversion_configuration_generator(sites_join, db_run)
        print (config)
        config.update()


def validate_inversion_configurations():
    db_runs = DatabaseObjects.InversionConfiguration.get_all()
    for db_run in db_runs:
        print (vars(db_run))

#populate_sites()
#populate_inversions()
#generate_offsets()
#validate_offsets()
#create_inversion_configurations()
validate_inversion_configurations()

'''
configuration = {
    'kalman_url': 'http://www.panga.org/realtime/data/api/',  # Not used, maybe future?
    'kalman_url_en': '?q=5min&l=',  # Not used, maybe future?
    'rabbit_mq_input': {'exchange_name': 'fastlane-nev-cov',
                  'host': 'pc96445.d.cwu.edu',
                  'userid': 'panga_ro',
                  'password': 'ro',
                  'virtual_host': '/CWU-ppp'},
    'rabbit_mq_output': {'exchange_name': 'slip-inversion2',
                         'host': 'pc96225.d.cwu.edu',
                         'port': 5672,
                         'userid': 'nif',
                         'virtual_host': '/rtgps-products',
                         'password': 'nars0add',
                         'model': 'Test'},
    'mongo_db_output': {'host': 'pc96225.d.cwu.edu',
                        'port': 27018,
                        'userid': 'nif',
                        'password': 'nars0add'},

'''