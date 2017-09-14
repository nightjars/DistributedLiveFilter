class KalmanConfiguration:

    def __init__(self, min_offset, max_offset, min_r, offset, eq_pause, eq_threshold, mes_wait, kill_limit):
        self.min_offset = min_offset
        self.max_offset = max_offset
        self.min_r = min_r
        self.offset = offset
        self.eq_pause = eq_pause
        self.eq_threshold = eq_threshold
        self.mes_wait = mes_wait
        self.kill_limit = kill_limit

    def __eq__(self, other):
        if isinstance(other, KalmanConfiguration):
            return self.min_offset == other.min_offset and \
                   self.max_offset == other.max_offset and \
                   self.min_r == other.min_r and \
                   self.offset == other.offset and \
                   self.eq_pause == other.eq_pause and \
                   self.eq_threshold == other.eq_threshold and \
                   self.mes_wait == other.mes_wait and \
                   self.kill_limit == other.kill_limit
        return NotImplemented

    def __ne__(self, other):
        result = self.__eq__(other)
        if result is NotImplemented:
            return result
        return not result
