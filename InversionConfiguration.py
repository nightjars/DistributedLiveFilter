import numpy as np
import ok
import copy

class InversionConfiguration:
    def __init__(self, faults):
        self.sub_inputs = None
        self.smooth_mat = None
        self.mask = None
        self.faults = faults

        # Store sites in both a list and map for efficient key search and sequencing
        self.site_map = {}
        self.site_list = []

        self.smoothing = None
        self.corner_fix = None
        self.short_smoothing = None
        self.convergence = None

    def get_site_index(self, site):
        return self.site_map[site]


def inversion_configuration_generator(site_data, old=None, faults=None, smoothing=None, corner_fix=None,
                                      short_smoothing=None, convergence=None):
    if old is None:
        if faults is None or smoothing is None or corner_fix is None or short_smoothing is None or convergence is None:
            return None

    configuration = InversionConfiguration(faults)

    if old is not None:
        configuration.smoothing = old.smoothing if smoothing is None else smoothing
        configuration.corner_fix = old.corner_fix if corner_fix is None else corner_fix
        configuration.short_smoothing = old.short_smoothing if short_smoothing is None else short_smoothing
        configuration.convergence = old.convergence if convergence is None else convergence
        configuration.site_map = copy.copy(old.site_map)
        configuration.site_list = copy.copy(old.site_list)
        configuration.sub_inputs = np.copy(old.sub_inputs)
    if faults is None:
        faults = old.faults
    subfault_wid = faults.width
    subfault_len = faults.length
    new_sub_input_data = {}
    for site in site_data:
        if site.name not in configuration.site_map:
            new_site_idx = len(configuration.site_list)
            new_sub_input_data[new_site_idx * 3] = []
            new_sub_input_data[new_site_idx * 3 + 1] = []
            new_sub_input_data[new_site_idx * 3 + 2] = []
            configuration.site_list.append(site)
            configuration.site_map[site.name] = new_site_idx
            for fault_idx, fault in enumerate(faults.fault_list):
                rake = fault.strike - convergence
                rake += 180
                if rake < 0:
                    rake += 360
                if rake > 360:
                    rake -= 360
                result = ok.dc3d(fault.lat, fault.lon, fault.depth, fault.strike, fault.dip, rake,
                                 fault.length, fault.width, 1, 0, site.lat, site.lon, 0)
                new_sub_input_data[new_site_idx * 3].append((fault_idx, float(result[0])))
                new_sub_input_data[new_site_idx * 3 + 1].append((fault_idx, float(result[1])))
                new_sub_input_data[new_site_idx * 3 + 2].append((fault_idx, float(result[2])))
    if configuration.sub_inputs is None:
        configuration.sub_inputs = np.zeros((len(configuration.site_list) * 3, len(faults.fault_list)))
    elif configuration.sub_inputs.shape[0] < len(configuration.site_list * 3):
        configuration.sub_inputs = configuration.sub_inputs.resize((len(configuration.site_list) * 3,
                                                                    len(faults.fault_list)))
    for idx, value in new_sub_input_data.items():
        for fault_result in value:
            fault_idx, result = fault_result
            configuration.sub_inputs[idx, fault_idx] = result

    if smoothing:
        if short_smoothing:
            for idx, fault in enumerate(faults.fault_list):
                configuration.smooth_mat[idx, idx] = 0
                if idx > subfault_len:
                    configuration.smooth_mat[idx, idx] = -1
                    configuration.smooth_mat[idx - subfault_len][idx] = 1
                    configuration.smooth_mat[idx, idx - subfault_len] = 1
                if idx < subfault_len * (subfault_wid - 1):
                    configuration.smooth_mat[idx, idx] -= 1
                    configuration.smooth_mat[idx + subfault_len, idx] = 1
                    configuration.smooth_mat[idx, idx + subfault_len] = 1
                if idx % subfault_len != 0:
                    configuration.smooth_mat[idx, idx] -= 1
                    configuration.smooth_mat[idx - 1, idx] = 1
                    configuration.smooth_mat[idx, idx - 1] = 1
                if idx % subfault_len != subfault_len - 1:
                    configuration.smooth_mat[idx, idx] -= 1
                    configuration.smooth_mat[idx + 1, idx] = 1
                    configuration.smooth_mat[idx, idx + 1] = 1
        else:
            raise NotImplementedError

        if corner_fix:
            for x in range(len(configuration.faults.fault_list)):
                configuration.smooth_mat[x, x] = -4

    configuration.mask[-len(configuration.faults.fault_list):, 0] = 1
    return configuration
