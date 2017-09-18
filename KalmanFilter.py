import numpy as np

class KalmanFilter:
    def __init__(self, configuration, site):
        self.configuration = configuration
        self.newest_measurement = 0
        self.cur_time = None
        self.prev_time = None
        self.site = site
        self.kill_count = 0
        self.h         = np.matrix([[1., 0., 0.], [0., 1., 0.], [0., 0., 1.]])
        self.phi       = np.matrix([[1., 0., 0.], [0., 1., 0.], [0., 0., 1.]])
        self.iden      = np.matrix([[1., 0., 0.], [0., 1., 0.], [0., 0., 1.]])
        self.k         = np.matrix([[0., 0., 0.], [0., 0., 0.], [0., 0., 0.]])
        self.m         = np.matrix([[0., 0., 0.], [0., 0., 0.], [0., 0., 0.]])
        self.r         = np.matrix([[0., 0., 0.], [0., 0., 0.], [0., 0., 0.]])
        self.state     = np.matrix([[0.], [0.], [0.]])
        self.state_2   = np.matrix([[0.], [0.], [0.]])
        self.p         = np.matrix([[1000., 0., 0.], [0., 1000., 0.], [0., 0., 1000.]])
        self.mea_mat   = np.matrix([[0.], [0.], [0.]])
        self.i_state   = np.matrix([[0.], [0.], [0.]])
        self.i_state_2 = np.matrix([[0.], [0.], [0.]])
        self.res       = np.matrix([[0.], [0.], [0.]])
        self.eq_count  = np.matrix([[0], [0], [0]])
        self.eq_flag   = np.matrix([[False], [False], [False]])
        self.reset_p   = np.matrix([[1000., 0., 0.], [0., 1000., 0.], [0., 0., 1000.]])
        self.synth_n       = 0.
        self.synth_e       = 0.
        self.synth_v       = 0.
        self.init_p        = 0
        self.p_count       = 0
        self.smooth_count  = 0
        self.start_up      = True
        self.offset        = False
        self.override_flag = False
        self.tag           = False
        self.output_state  = None
        self.output_flag   = False
        self.s_measure     = []


    def process_measurement(self, measurement):
        self.output_flag = False
        self.output_state = None
        if self.newest_measurement < measurement.t:
            self.prev_time = self.newest_measurement
            self.newest_measurement = measurement.t
            self.cur_time = measurement.t
            if measurement.n != 0. or measurement.e != 0. or measurement.v != 0.:
                cn = measurement.cn
                cv = measurement.cv
                ce = measurement.ce
                n = measurement.n
                e = measurement.e
                v = measurement.v
                r = np.matrix([[cn, 0., 0.],
                               [0., ce, 0.],
                               [0., 0., cv]])
                mea_mat = np.matrix([[n], [e], [v]])
                res = mea_mat - self.h * self.phi * self.state - \
                                self.h * self.phi * self.state_2
                if np.abs(res[0, 0]) < self.configuration.max_offset and \
                    np.abs(res[1, 0]) < self.configuration.max_offset and \
                    np.abs(res[2, 0]) < self.configuration.max_offset:
                    self.kill_count = 0
                    if self.prev_time == 0:
                        self.state_2 = mea_mat * 1.0
                    else:
                        self.prev_time = self.cur_time
                        self.mea_mat = mea_mat
                        r[0, 0] = max(r[0, 0], self.configuration.min_r)
                        r[1, 1] = max(r[1, 1], self.configuration.min_r)
                        r[2, 2] = max(r[2, 2], self.configuration.min_r)
                        self.r = r
                        if self.offset:
                            self.pass_update_state()
                        else:
                            self.update_matrix()
                        if self.output_flag:
                            return self.output_state
                        else:
                            return None
                else:
                    self.kill_count += 1
                    # log
            else:
                pass
        else:
            pass
        return None

    def update_matrix(self):
        delta_t = self.cur_time - self.prev_time
        self.prev_time = self.cur_time
        q = np.matrix([[delta_t, 0., 0.], [0., delta_t, 0.], [0., 0., delta_t]])
        self.m = self.phi * self.p * self.phi.T + q
        interm = (self.h * self.m * self.h.T + self.r).I
        self.k = self.m * self.h.T * interm
        self.p = (self.iden - self.k * self.h) * self.m
        self.calc_res()

    def calc_res(self):
        self.res = self.mea_mat - self.h * self.phi * self.state - \
                   self.h * self.phi * self.state_2
        if not self.override_flag:
            self.determine_state()

    def determine_state(self):
        if self.smooth_count >= self.configuration.eq_pause and self.start_up:
            self.start_up = False
        if self.smooth_count < self.configuration.eq_pause:
            self.eq_count = np.matrix([[0], [0], [0]])
            self.normal_mode()
            self.end_proc()
        else:
            if np.abs(self.res[0, 0]) < np.sqrt(self.r[0, 0]) * self.configuration.eq_threshold:
                self.eq_flag[0, 0] = False
                self.eq_count[0, 0] = 0
            else:
                self.eq_flag[0, 0] = True
                self.eq_count[0, 0] += 1
            if np.abs(self.res[1, 0]) < np.sqrt(self.r[1, 1]) * self.configuration.eq_threshold:
                self.eq_flag[1, 0] = False
                self.eq_count[1, 0] = 0
            else:
                self.eq_flag[1, 0] = True
                self.eq_count[1, 0] += 1
            if np.abs(self.res[2, 0]) < np.sqrt(self.r[2, 2]) * self.configuration.eq_threshold:
                self.eq_flag[2, 0] = False
                self.eq_count[2, 0] = 0
            else:
                self.eq_flag[2, 0] = True
                self.eq_count[2, 0] += 1
            if self.eq_flag_test() \
                    and self.eq_num_test() > self.configuration.mes_wait \
                    and self.offset:
                self.eq_state()
            elif self.offset and not self.eq_flag_test():
                self.false_eq_state()
            elif self.eq_flag_test() and not self.offset:
                self.begin_eq_test_state()
            else:
                self.normal_mode()
                self.end_proc()

    def normal_mode(self):
        self.state = self.phi * self.state + self.k * self.res
        self.state_2 = self.phi * self.state_2
        self.tag = True if self.smooth_count < self.configuration.eq_pause and not self.start_up \
            else False
        self.output_state = self.generate_output_state()

    def end_proc(self):
        if self.offset:
            self.s_measure.append((self.cur_time, self.mea_mat, self.r))
        else:
            self.smooth_count += 1
            self.normal_mode()
        self.output_flag = True

    def begin_eq_test_state(self):
        self.offset = True
        self.pass_state_start()

    def eq_state(self):
        self.offset_reset()
        self.smooth_count = 0
        self.s_measure.append((self.cur_time, self.mea_mat, self.r))
        self.init_p = self.p[0, 0]
        self.p = self.reset_p * 1.0
        self.p_count = 0
        self.offset = False
        self.override_flag = True
        for mea in self.s_measure[:-1]:
            self.cur_time, self.mea_mat, self.r = mea
            self.update_matrix()
            self.normal_mode()
        self.cur_time, self.mea_mat, self.r = self.s_measure[-1]
        self.s_measure = []
        self.override_flag = False

    def false_eq_state(self):
        self.end_pass_state()
        self.override_flag = True
        self.s_measure.append((self.cur_time, self.mea_mat, self.r))
        for mea in self.s_measure[:-1]:
            self.cur_time, self.mea_mat, self.r = mea
            self.calc_res()
            self.normal_mode()
            self.update_matrix()
        self.cur_time, self.mea_mat, self.r = self.s_measure[-1]
        self.s_measure = []
        self.offset = False
        self.override_flag = False

    def offset_reset(self):
        self.state_2 = self.i_state + self.i_state_2
        self.state = np.matrix([[0.], [0.], [0.]])

    def pass_state_start(self):
        self.i_state = self.state * 1.
        self.i_state_2 = self.state_2 * 1.

    def pass_update_state(self):
        self.state = self.phi * self.state
        self.state_2 = self.phi * self.state_2
        self.calc_res()

    def end_pass_state(self):
        self.state = self.i_state * 1.
        self.state_2 = self.i_state_2 * 1.

    def eq_flag_test(self):
        return any(self.eq_flag[0:3, 0])

    def eq_num_test(self):
        return max(self.eq_count[0:3, 0])

    def generate_output_state(self):
        return {
            'site': self.site,
            'la': None,
            'lo': None,
            'mn': self.mea_mat[0, 0],
            'me': self.mea_mat[1, 0],
            'mv': self.mea_mat[2, 0],
            'kn': self.state[0, 0],
            'ke': self.state[1, 0],
            'kv': self.state[2, 0],
            'cn': self.r[0, 0],
            'ce': self.r[1, 1],
            'cv': self.r[2, 2],
            'he': 0,
            'ta': self.tag,
            'st': self.start_up,
            'time': self.cur_time
        }

'''
        {
            'site': None,
            'prev_time': None,
            'delta_t': delta_t,
            'max_offset': run['max_offset'],
            'last_calculation': None,
            'measurement_queue': queue.PriorityQueue(),
            'lock': threading.Lock(),
            'sites': run['sites'],
            'faults': faults,
            'def_r': run['min_r'],
            'offset': run['offset'],
            'q': np.matrix([[delta_t, 0., 0.], [0., delta_t, 0.], [0., 0., delta_t]]),
            'res': np.matrix([[0.], [0.], [0.]]),
            'override_flag': False,
            'sm_count': 0,
            'smoothing': run['eq_pause'],
            'start_up': True,
            'eq_count': np.matrix([[0], [0], [0]]),
            'eq_flag': np.matrix([[False], [False], [False]]),
            'eq_threshold': run['eq_threshold'],
            'tag': False,
            's_measure': [],
            'init_p': 0,
            'reset_p': np.matrix([[1000., 0., 0.], [0., 1000., 0.], [0., 0., 1000.]]),
            'p_count': 0,
            'time': 0,
            'write': '',
            'data_set': [],
            'wait': run['mes_wait'],
            'run': run,
            'temp_kill_limit': 100,
            'temp_kill': 0
        # temporary solution for problem with kalman filter state/state2 causing measurements to be ignored
        }
'''