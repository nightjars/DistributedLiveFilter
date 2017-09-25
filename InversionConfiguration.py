import numpy as np
import ok
import copy
import DatabaseObjects

def inversion_configuration_generator(site_data, inversion_config):
    if inversion_config is None:
        return None

    faults = inversion_config.faults

    if inversion_config is None or not \
            isinstance(inversion_config.site_map, dict):
        inversion_config.site_map = {}

    new_sub_input_data = {}
    for site in site_data:
        if site.name not in inversion_config.site_map:
            new_site_idx = len(inversion_config.site_map)
            new_sub_input_data[new_site_idx * 3] = []
            new_sub_input_data[new_site_idx * 3 + 1] = []
            new_sub_input_data[new_site_idx * 3 + 2] = []
            inversion_config.site_map[site.name] = new_site_idx
            for fault_idx, fault in enumerate(faults.fault_list):
                rake = fault.strike - inversion_config.convergence
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
    if inversion_config.sub_inputs is None:
        inversion_config.sub_inputs = np.zeros((len(inversion_config.site_map) * 3, len(faults.fault_list)))
    elif inversion_config.sub_inputs.shape[0] < len(inversion_config.site_map) * 3:
        inversion_config.sub_inputs = inversion_config.sub_inputs.resize(len(inversion_config.site_map) * 3,
                                                                    len(faults.fault_list))
    for idx, value in new_sub_input_data.items():
        for fault_result in value:
            fault_idx, result = fault_result
            inversion_config.sub_inputs[idx, fault_idx] = result

    inversion_config.offset = np.zeros((len(site_data) * 3) + len(faults.fault_list))
    inversion_config.mask = np.zeros(((len(site_data) * 3) + len(faults.fault_list), 1))
    inversion_config.sub_inputs = np.zeros((len(site_data) * 3, len(faults.fault_list)))
    inversion_config.smooth_mat = np.zeros((len(faults.fault_list), len(faults.fault_list)))

    if inversion_config.smoothing:
        if inversion_config.short_smoothing:
            for idx, fault in enumerate(faults.fault_list):
                inversion_config.smooth_mat[idx, idx] = 0
                if idx > faults.width:
                    inversion_config.smooth_mat[idx, idx] = -1
                    inversion_config.smooth_mat[idx - faults.length][idx] = 1
                    inversion_config.smooth_mat[idx, idx - faults.length] = 1
                if idx < faults.length * (faults.width - 1):
                    inversion_config.smooth_mat[idx, idx] -= 1
                    inversion_config.smooth_mat[idx + faults.length, idx] = 1
                    inversion_config.smooth_mat[idx, idx + faults.length] = 1
                if idx % faults.length != 0:
                    inversion_config.smooth_mat[idx, idx] -= 1
                    inversion_config.smooth_mat[idx - 1, idx] = 1
                    inversion_config.smooth_mat[idx, idx - 1] = 1
                if idx % faults.length != faults.length - 1:
                    inversion_config.smooth_mat[idx, idx] -= 1
                    inversion_config.smooth_mat[idx + 1, idx] = 1
                    inversion_config.smooth_mat[idx, idx + 1] = 1
        else:
            raise NotImplementedError

        if inversion_config.corner_fix:
            for x in range(len(inversion_config.faults.fault_list)):
                inversion_config.smooth_mat[x, x] = -4

        inversion_config.mask[-len(inversion_config.faults.fault_list):, 0] = 1
    return inversion_config
