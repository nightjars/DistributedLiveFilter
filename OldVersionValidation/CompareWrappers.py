import dist_filt
import ok
import numpy as np
import math
import oldok

def load_data_from_text_files():

    sites_dict = {}
    with open ('CAS_offset.d') as file:
        sites = [x.split() for x in file.readlines() if x[0] != '#']

    for site in sites:
        station = {
            'name': site[0],
            'lat': float(site[1]),
            'lon': float(site[2]),
            'height': float(site[3]),
            'offset': float(site[4]),
            'index': len(sites_dict)                            # store index for array sequencing
        }


        if station['name'] not in sites_dict:
            sites_dict[station['name']] = station

    # Allow appending new stations once programming is running without having to iterate through
    # full list of sites by storing last-used-index
    # sites_dict['max_index'] = len(sites)

    with open('CAS_faults.d') as file:
        fault_data = [x.split() for x in file.readlines() if x[0] != '#']


    faults = {
        'length': float(fault_data[0][0]),
        'width': float(fault_data[0][1]),
        'subfault_list': [[float(x) for x in fault_data_line] for fault_data_line in fault_data[1:]]
    }
    return (sites_dict, faults)

def mangle(fault_lat, fault_lon, fault_depth, fault_strike, fault_dip,
            rake, fault_len, fault_wid, slip, site_lat, site_lon):


    dlat = 110.574 * abs(fault_lat - site_lat)
    dlon = 111.32 * math.cos(fault_lat * np.pi / 180)

    dis = (dlat ** 2 + dlon ** 2) ** 0.5

    if dis < 1000:

        # print("Dis = {}".format(dis))
        # print("./defpt.pl {} {} {} {} {} {} {} {} {} {} {} {} {}".format(lat, lon, dep, strike, dip, rak, length, wid, slip, ten_slip, olat, olon, odep ))
        out2 = ok.dc3d(fault_lat, fault_lon, fault_depth, fault_strike, fault_dip,
                rake, fault_len, fault_wid, slip, 0, site_lat, site_lon, 0)    # print("this is out: {}".format(out))

        out2 = oldok.dc3d(fault_lat, fault_lon, fault_depth, fault_strike, fault_dip,
                       rake, fault_len, fault_wid, slip, 0, site_lat, site_lon, 0)

        dx = float(out2[0])
        dy = float(out2[1])
        dz = float(out2[2])

        mag = np.sqrt(dx ** 2 + dy ** 2 + dz ** 2)

    else:
        mag = -100.0
    # print("this is out2: {}".format(out2))
    return (mag)

def mangle2(fault_lat, fault_lon, fault_depth, fault_strike, fault_dip,
            rake, fault_len, fault_wid, slip, site_lat, site_lon):


    dlat = 110.574 * abs(fault_lat - site_lat)
    dlon = 111.32 * math.cos(fault_lat * np.pi / 180)

    dis = (dlat ** 2 + dlon ** 2) ** 0.5

    if dis < 1000:

        # print("Dis = {}".format(dis))
        #l print("./defpt.pl {} {} {} {} {} {} {} {} {} {} {} {} {}".format(lat, lon, dep, strike, dip, rak, length, wid, slip, ten_slip, olat, olon, odep ))
        #out2 = ok.dc3d(fault_lat, fault_lon, fault_depth, fault_strike, fault_dip,
        #        rake, fault_len, fault_wid, slip, 0, site_lat, site_lon, 0)    # print("this is out: {}".format(out))

        out2 = oldok.dc3d(fault_lat, fault_lon, fault_depth, fault_strike, fault_dip,
                       rake, fault_len, fault_wid, slip, 0, site_lat, site_lon, 0)

        dx = float(out2[0])
        dy = float(out2[1])
        dz = float(out2[2])

        mag = np.sqrt(dx ** 2 + dy ** 2 + dz ** 2)

    else:
        print (dis)
        mag = 0.0
    # print("this is out2: {}".format(out2))
    return (mag)

def compare():
    sites, faults = load_data_from_text_files()
    print (sites)
    for _, site in sites.items():
        site_name = site['name']
        site_lat = site['lat']
        site_lon = site['lon']
        site_ele = site['height']
        max_mag = 0
        max_mag2 = 0
        for fault in faults['subfault_list']:
            fault_lat, fault_lon, fault_depth, fault_strike, fault_dip, fault_len, fault_wid ,_ , _ = fault
            slip = 1  # from example usage, not sure what this means
            rake = 180  # from example usage, not sure why real rake value isn't used
            mag = mangle(fault_lat, fault_lon, fault_depth, fault_strike, fault_dip,
                    rake, fault_len, fault_wid, slip, site_lat, site_lon)
            #mag2 = mangle2(fault_lat, fault_lon, fault_depth, fault_strike, fault_dip,
            #        rake, fault_len, fault_wid, slip, site_lat, site_lon)
            mag2 = dist_filt.adp(fault_lat, fault_lon, fault_depth, fault_strike, fault_dip,
                    rake, fault_len, fault_wid, slip, site_lat, site_lon)
            max_mag = max(mag, max_mag)
            max_mag2 = max(mag2, max_mag2)

        if math.isclose(max_mag, max_mag2, abs_tol=1e-04) and \
            math.isclose(max_mag, site['offset'], abs_tol=1e-04):
            print ("{} ok".format(site_name))
        else:
            print ("{} {} {} {} {} {}".format(site_name, max_mag, max_mag2, site['offset'], max_mag - max_mag2,
                                          max_mag - site['offset']))

#compare()