import json
import calendar
import time
import Measurement
import KalmanConfiguration
import KalmanFilter
import OldVersionValidation.Config as old_config
import OldVersionValidation.Kalman as old_kalman
import queue
import logging

class ConfigurationMapEntry:
    def __init__(self, configuration):
        self.configuration = configuration
        self.filters = {}

class WorkerFilter:
    def __init__(self):
        self.filter_map = {}

    def add_configuration(self, id, new_configuration):
        self.filter_map[id] = ConfigurationMapEntry(new_configuration)

    def remove_filter(self, id, site_name):
        filter_state = None
        if id in self.filter_map:
            if site_name in self.filter_map[id].filters:
                filter_state = self.filter_map[id].filters[site_name]
                del self.filter_map[id].filters[site_name]
        return filter_state

    def add_filter(self, id, site_name, filter_state=None):
        if site_name not in self.filter_map[id].filters:
            if filter_state is None:
                self.filter_map[id].filters[site_name] = KalmanFilter.KalmanFilter(
                    self.filter_map[id].configuration, site_name)
            else:
                self.filter_map[id].filters[site_name] = filter_state

    def process_measurements(self, measurement_list):
        results = []
        for (configuration, measurement) in measurement_list:
            if configuration in self.filter_map:
                if measurement.site in self.filter_map[configuration].filters:
                    result = self.filter_map[configuration].filters[measurement.site].process_measurement(measurement)
                    if result is not None:
                        results.append((configuration, result))
            else:
                pass
        return results




# Crude test code to verify kalman filter output matches known good kalman filter code
if __name__ == "__main__":
    run = {
        'sites_file': './SA_offset.d',
        'faults_file': './SA_faults.d',
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
    }
    logging.basicConfig(level=logging.INFO)
    logging.info('hi')
    old_q = queue.Queue()
    conf = KalmanConfiguration.KalmanConfiguration(0.001, 4000, 0.0001, 10., 0.01, 2, 100)
    wf = WorkerFilter()
    wf.add_configuration(1, conf)
    with open("out_600_sec") as f:
        data = json.load(f)

    init_time = None
    last = 0
    mea_send = []
    old_kalman = old_kalman.KalmanThread(None, old_q)
    old_kal_map = {}
    for d in data:
        if init_time is None:
            init_time = calendar.timegm(time.gmtime()) - d['t']
        d['t'] += init_time
        mea = Measurement.Measurement(**d)
        mea_send.append((1, mea))
        if not d['site'] in old_kal_map:
            old_kal_map[d['site']] = old_config.get_empty_kalman_state(run)
            old_kal_map[d['site']]['site'] = {'name': d['site'], 'lat': None, 'lon': None}
        old_kal_map[d['site']]['data_set'].append(d)
        old_kalman.process_measurement(old_kal_map[d['site']])
        if d['t'] > last:
            last = d['t']
            #time.sleep(.8)
            a = [mea for conf, mea in wf.process_measurements(mea_send)]
            b = []
            try:
                while old_q.not_empty:
                    _, data_in, _ = old_q.get_nowait()
                    b.append(data_in)
            except:
                pass
            print (len(a), " ", len(b))
            for idx, d in enumerate(a):
                if a[idx] != b[idx]:
                    print(idx)
                    print(a[idx])
                    print(b[idx])
                    print(vars(wf.filter_map[1].filters[a[idx]['site']]))
                    print(old_kal_map[a[idx]['site']])
                    exit()
            mea_send = []