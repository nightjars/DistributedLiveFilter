class Measurement:

    def __init__(self, t, site, cnv, e, cn, ce, n, cev, cne, v, cv):
        self.t = t
        self.site = site
        self.cnv = cnv
        self.e = e
        self.cn = cn
        self.ce = ce
        self.n = n
        self.cev = cev
        self.cne = cne
        self.v = v
        self.cv = cv

    '''        
    new_data = {
        't': cur_time,
        'site': site_list[random.randint(0, len(site_list) - 1)],
        'cnv': random.random() * 2 - 1,
        'e': .3 + random.random() * .1 - .05,
        'cn': 0.0001 + random.random() * .002 - .001,
        'ce': 0.0001 + random.random() * .002 - .001,
        'n': .3 + random.random() * .1 - .05,
        'cev': random.random() * 4 - 2,
        'cne': random.random() * 2 - 1,
        'v': .3 + random.random() * .1 - .05,
        'cv': 0.0001 + random.random() * .002 - .001
    }
    '''