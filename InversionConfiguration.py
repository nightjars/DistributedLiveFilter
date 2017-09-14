import numpy
import threading

class InversionConfiguration:
    def __init__(self, faults):
        self.offset = None
        self.sub_inputs = None
        self.smooth_mat = None
        self.mask = None
        self.faults = faults

        # Store sites in both a list and map for efficient key search and sequencing
        self.site_map = {}
        self.site_list = []

    def get_site_index(self, site):
        site_ele = self.site_map[site]
        return site_ele['idx']

