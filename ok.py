import ok1
import numpy as np
from math import cos, sin, log10

def dc3d( lat, lon, depth, strike, dip, rake, fault_length, fault_width, fault_slip, tensile_slip, obs_lat, obs_lon, obs_dep ):
    if lon > 180:
        lon -= 360
    if obs_lon > 180:
        obs_lon -= 360
    if rake < 0:
        rake += 360
    if rake > 360:
        rake -= 360

    # convert to okada format
    al1 = -fault_length / 2;
    al2 = fault_length / 2;
    aw1 = -fault_width / 2;
    aw2 = fault_width / 2;

    SS = (fault_slip * cos((rake) * .01744))
    DS = (fault_slip * sin((180 - rake) * .01744))

    MU = float( 3e11 )
    EARTH_CIRCUM = 40000
    PI = 3.14159

    pz = obs_dep

    strike = strike/180*PI
    lat_rad = lat/180*PI
    lon_rad = lon/180*PI
    obs_lat_rad = obs_lat/180*PI
    obs_lon_rad = obs_lon/180*PI

    easting = 111 * cos(lat_rad) * (obs_lon-lon)
    northing = 111 * (obs_lat - lat)
    px = northing * cos(strike) + easting * sin(strike)
    py = -easting * cos(strike) + northing * sin(strike)

    result = ok1.dc3d(0.66666, np.float32(px), np.float32(py), np.float32(pz),
                     np.float32(depth),np.float32(dip), np.float32(al1), np.float32(al2),
                     np.float32(aw1), np.float32(aw2), np.float32(SS), np.float32(DS), np.float32(tensile_slip))

    ux, uy, uz, uxx, uyx, uzx, uxy, uyy, uzy, uxz, uyz, uzz, iiret = (np.float32(x) for x in result)
    def_pt_rot_east = -uy*cos(strike) + ux * sin(strike)
    def_pt_rot_north = uy * sin(strike) + ux*cos(strike)
    def_pt_rot_vertical = uz
    def_pt_rot_dzdn = uzx * cos(strike) + uzy*sin(strike)
    def_pt_rot_dzde = uzx * sin(strike) - uzy*cos(strike)
    moment = MU * ((SS ** 2 + DS ** 2 + tensile_slip ** 2) ** .5) * 100 * ((aw2 - aw1) * 1e5 * \
             (al2 - al1) * 1e5)
    moment_mag = log10(moment)/1.5-10.73
    stress_drop = (2 * MU * (SS ** 2 + DS ** 2 + tensile_slip ** 2) ** .5 * 100 * \
                  ((aw2 - aw1) * 1e5 * (al2 - al1) * 1e5) ** .5) / 1e6

    return def_pt_rot_north, def_pt_rot_east, def_pt_rot_vertical, def_pt_rot_dzdn, def_pt_rot_dzde, \
           moment, moment_mag, stress_drop
