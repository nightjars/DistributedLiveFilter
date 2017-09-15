class Fault:
    def __init__(self, lat, lon, depth, strike, dip, length, width, unk):
        self.lat = lat
        self.lon = lon
        self.depth = depth
        self.strike = strike
        self.dip = dip
        self.length = length
        self.width = width
        self.unk = unk

class SolutionFaults:
    def __init__(self, length, width, fault_list):
        self.length = length
        self.width = width
        self.fault_list = fault_list