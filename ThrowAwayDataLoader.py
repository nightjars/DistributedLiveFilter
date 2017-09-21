import DatabaseObjects
import Site
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
                    DatabaseObjects.save_site(vars(Site.Site(name, lat, lon, ele)))
                except:
                    pass


def populate_inversions():
    for run in inversion_runs:
        with open(run['faults_file']) as file:
            fault_data = [x.split() for x in file.readlines() if x[0] != '#']

        faults_dict = {
            'length': float(fault_data[0][0]),
            'width': float(fault_data[0][1]),
            'subfault_list': [[float(x) for x in fault_data_line] for fault_data_line in fault_data[1:]]
        }

        fault_object_list = []
        for subfault in faults_dict['subfault_list']:
            fault_object_list.append(Fault.Fault(subfault[0], subfault[1], subfault[2], subfault[3], subfault[4],
                                                 subfault[5], subfault[6], subfault[7]))
        faults = Fault.SolutionFaults(faults_dict['length'], faults_dict['width'], fault_object_list)
        conf = InversionConfiguration.InversionConfiguration(faults, run['model'], run['label'], run['tag'])
        conf.smoothing = run['inverter_configuration']['smoothing']
        conf.corner_fix = run['inverter_configuration']['corner_fix']
        conf.short_smoothing = run['inverter_configuration']['short_smoothing']
        conf.convergence = run['convergence']
        print (vars(conf))
        DatabaseObjects.save_inversion(vars(conf))

def generate_offsets():
    inversions = DatabaseObjects.get_inversions()

    session = DatabaseObjects.get_db_session()

    for inversion in inversions:
        print (inversion)
        for site in session.query(DatabaseObjects.Site)\
                .outerjoin(DatabaseObjects.SiteInversionAssociation)\
                .filter(~exists().where(DatabaseObjects.SiteInversionAssociation.inversion_id == inversion.id)):
            max_mag = 0
            for fault in inversion.faults.fault_list:
                slip = 1  # from example usage, not sure what this means
                rake = 180  # from example usage, not sure why real rake value isn't used

                mag = CompareWrappers.mangle\
                    (fault.lat, fault.lon, fault.depth, fault.strike, fault.dip,
                     rake, fault.length, fault.width, slip, site.lat, site.lon)

                max_mag = max(mag, max_mag)
            a = DatabaseObjects.SiteInversionAssociation()
            a.inversion = inversion
            a.site = site
            a.offset = max_mag
            session.add(a)
            session.commit()
            print("{} {} {}".format(site.name, inversion.model, max_mag))

def validate_offsets():
    session = DatabaseObjects.get_db_session()
    for run in inversion_runs:
        #print (run['model'])
        db_run = session.query(DatabaseObjects.InversionConfiguration).filter(
            DatabaseObjects.InversionConfiguration.model == run['model'])[0]
        print (db_run.model)
        with open(run['sites_file'], "r") as f:
            sites = f.readlines()
            for site in sites:
                name, lat, lon, ele, mag = site.split()
                #if name == 'ALBH':
                mag = float(mag)
                site = session.query(DatabaseObjects.Site).filter(DatabaseObjects.Site.name == name)[0]
                site_inv_join = session.query(DatabaseObjects.SiteInversionAssociation).filter(and_(
                    DatabaseObjects.SiteInversionAssociation.site_id == site.id,
                    DatabaseObjects.SiteInversionAssociation.inversion_id == db_run.id))[0]
                db_mag = site_inv_join.offset
                #print (db_run.id)
                #print(vars(site))
                #print (vars(site_inv_join))
                diff = mag - db_mag
                if abs(diff) > 0.0005:
                    print ("{} {} {}".format(site.name, mag, db_mag))
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
                    print (max_mag)
                    print (max_mag2)

def create_inversion_configurations():
    session = DatabaseObjects.get_db_session()
#populate_sites()
#populate_inversions()
#generate_offsets()
#validate_offsets()

