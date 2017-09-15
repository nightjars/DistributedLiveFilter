import numpy as np
import math
from scipy import optimize

class Inversion:
    def __init__(self, configuration):
        self.configuration = configuration

    def invert(self, data_set):
        site_correlate = []
        offset = np.copy(self.configuration.offset)
        sub_inputs = np.copy(self.configuration.sub_inputs)
        mask = np.copy(self.configuration.mask)
        smooth_mat = self.configuration.smooth_mat
        for _, kalman_filter_output in data_set.items():
            site_idx = self.configuration.get_site_index(kalman_filter_output['site'])
            site_correlate.append((site_idx, kalman_filter_output['site']))
            mask[site_idx * 3: site_idx * 3 + 3, 0] = 1
            if kalman_filter_output['ta']:
                offset[site_idx * 3] = kalman_filter_output['kn']
                offset[site_idx * 3 + 1] = kalman_filter_output['ke']
                offset[site_idx * 3 + 2] = kalman_filter_output['kv']
            else:
                offset[site_idx * 3: site_idx * 3 + 3] = 0
        site_correlate.sort(key=lambda idx: idx[0])

        # Remove the elements from sub_inputs, etc, that are not part of this
        # data set
        valid_site_indexes = np.argwhere(mask[:len(
            self.configuration.site_list) * 3, 0] > 0)[:, 0]
        valid_site_fault_indexes = np.argwhere(mask[:, 0] > 0)[:, 0]
        present_sub_inputs = sub_inputs[valid_site_indexes, :]
        sub_inputs = np.vstack([present_sub_inputs, smooth_mat])
        present_offsets = offset[valid_site_fault_indexes]

        # Perform matrix math now that only extant sites are part of the solution
        solution = optimize.nnls(sub_inputs, present_offsets)[0]
        calc_offset = sub_inputs.dot(solution)
        return self.generate_output(solution, data_set, site_correlate, calc_offset)

    def generate_output(self, solution, data_set, site_correlate, calc_offset)
        faults = self.configuration.faults
        fault_sol = []
        magnitude = 0.0
        final_calc = []
        site_data = []
        slip = []
        estimates = []
        time_stamp = 0

        for idx, sol in enumerate(solution):
            fault_sol.append([
                self.configuration.faults.fault_list[idx].lat,
                self.configuration.faults.fault_list[idx].lon,
                self.configuration.faults.fault_list[idx].depth,
                self.configuration.faults.fault_list[idx].strike,
                self.configuration.faults.fault_list[idx].dip,
                str(self.configuration.faults.fault_list[idx].unk),
                self.configuration.faults.fault_list[idx].length,
                self.configuration.faults.fault_list[idx].width,
                str(sol),
                "0",
                sol])
            magnitude += float(fault_sol[-1][6]) * float(fault_sol[-1][7]) * float(1e12) * \
                         np.abs(float(fault_sol[-1][8]))
        magnitude *= float(3e11)

        for fault in fault_sol:
            slip.append(fault)

        for idx, site in enumerate(site_correlate):
            _, site_name = site  # split up tuple of site_idx,site
            kalman_site = data_set[site_name]
            time_stamp = max(kalman_site['t'], time_stamp)
            final_calc.append([
                kalman_site['site'],
                kalman_site['la'],
                kalman_site['lo'],
                kalman_site['he'],
                kalman_site['kn'] if kalman_site['ta'] else 0,
                kalman_site['ke'] if kalman_site['ta'] else 0,
                kalman_site['kv'] if kalman_site['ta'] else 0,
                calc_offset[idx * 3],
                calc_offset[idx * 3 + 1],
                calc_offset[idx * 3 + 2],
            ])
            site_data.append([
                kalman_site['site'],
                kalman_site['kn'],
                kalman_site['ke'],
                kalman_site['kv'],
                kalman_site['ta'],
                kalman_site['mn'],
                kalman_site['me'],
                kalman_site['mv'],
                kalman_site['cn'],
                kalman_site['ce'],
                kalman_site['cv'],
            ])

        for calc in final_calc:
            estimates.append(calc[0:10])

        mw = "NA" if math.isclose(0, magnitude) else \
            "{:.1f}".format(2 / 3. * np.log10(magnitude) - 10.7)
        magnitude_str = "{:.2E}".format(magnitude)

        return {
            'time': time_stamp,
            'data': site_data,
            'label': "label and model to appear" + dt.utcfromtimestamp(float(time_stamp)).strftime(
                "%Y-%m-%d %H:%M:%S %Z"),
            'slip': slip,
            'estimates': estimates,
            'Moment': magnitude_str,
            'Magnitude': mw
        }