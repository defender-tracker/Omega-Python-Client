import json
import logging
import copy
import datetime
import decimal


def get_epoch_time(t, d):
    # get_epoch_time converts time data from SNS message into epoch time

    return int(datetime.datetime.strptime(
        str(d.day) + "-" + str(d.month) + "-" + str(d.year) + " " + str(t.hour) + ":" + str(t.minute) + ":" + str(t.second), '%d-%m-%Y %H:%M:%S').timestamp())


def convert_lat_long(value, dir):
    # convert_lat_long takes the NMEA formatted location data and converts it into decimal latitude and longitude.

    deg, dec = value.split('.')
    precision = len(dec)
    mins = deg[-2:] + '.' + dec
    comp = float(mins) / 60 + float(deg[:-2])
    comp = comp if (dir is 'E' or dir is 'N') else (comp / -1)
    return round(float(str(comp)), precision)


class GNSS_Blob:

    def __init__(self):
        self.reset()

    def reset(self):
        self.information = {
            'satellites': {},
            'fix': {},
            'track_and_speed': {},
            'dop': {},
            'transit_data': {}
        }

    def add_satellite(self, msg):
        self.locked = False
        keys = [
            'num_messages',
            'msg_num',
            'num_sv_in_view',
            'sv_prn_num_1',
            'elevation_deg_1',
            'azimuth_1',
            'snr_1'	,
            'sv_prn_num_2',
            'elevation_deg_2',
            'azimuth_2',
            'snr_2',
            'sv_prn_num_3',
            'elevation_deg_3',
            'azimuth_3',
            'snr_3',
            'sv_prn_num_4',
            'elevation_deg_4',
            'azimuth_4',
            'snr_4'
        ]
        for key in keys:
            try:
                if msg.msg_num == 1:
                    self.reset()

                if msg.msg_num not in self.information['satellites']:
                    self.information['satellites'][msg.msg_num] = {}

                self.information['satellites'][msg.msg_num][key] = getattr(
                    msg, key)
            except Exception as e:
                logging.error(e)
                continue

    def check_satellites(self):
        self.locked = True
        num_messages = -1
        msg_num_sum = 0

        for sat_num, sat_info in self.information['satellites'].items():
            try:
                if int(sat_num) != int(sat_info['msg_num']):
                    self.locked = False

                if num_messages < 0:
                    num_messages = int(sat_info['num_messages'])
                elif num_messages != int(sat_info['num_messages']):
                    self.locked = False

                msg_num_sum += int(sat_info['msg_num'])
            except KeyError as ke:
                print("KeyError")
                print(ke)
                self.locked = False
                break
            except Exception as e:
                print("Error")
                print(e)
                self.locked = False
                break

        if msg_num_sum != sum(range(num_messages+1)) and len(self.information['satellites']) != num_messages:
            self.locked = False

        return self.locked

    def add_fix_data(self, msg):

        keys = [
            'timestamp',
            'lat',
            'lat_dir',
            'lon',
            'lon_dir',
            'gps_qual',
            'num_sats',
            'horizontal_dil',
            'altitude',
            'altitude_units',
            'geo_sep',
            'geo_sep_units',
            'age_gps_data',
            'ref_station_id'
        ]

        for key in keys:
            try:
                self.information['fix'][key] = getattr(msg, key)
            except:
                continue

    # Track made good and ground speed
    def add_track_and_ground_speed(self, msg):

        keys = [
            'true_track',
            'true_track_sym',
            'mag_track',
            'mag_track_sym',
            'spd_over_grnd_kts',
            'spd_over_grnd_kts_sym',
            'spd_over_grnd_kmph',
            'spd_over_grnd_kmph_sym',
            'faa_mode'
        ]

        for key in keys:
            try:
                self.information['track_and_speed'][key] = getattr(msg, key)
            except:
                continue

    # Recommended minimum specific GPS/Transit data
    def add_minimum_transit_data(self, msg):

        keys = [
            'timestamp',
            'status',
            'lat',
            'lat_dir',
            'lon',
            'lon_dir',
            'spd_over_grnd',
            'true_course',
            'datestamp',
            'mag_variation',
            'mag_var_dir'
        ]

        for key in keys:
            try:
                self.information['transit_data'][key] = getattr(msg, key)
            except:
                continue

    # GPS DOP and active satellites
    def add_DOP(self, msg):
        keys = [
            'mode',
            'mode_fix_type',
            'sv_id01',
            'sv_id02',
            'sv_id03',
            'sv_id04',
            'sv_id05',
            'sv_id06',
            'sv_id07',
            'sv_id08',
            'sv_id09',
            'sv_id10',
            'sv_id11',
            'sv_id12',
            'pdop',
            'hdop',
            'vdop'
        ]

        for key in keys:
            try:
                self.information['dop'][key] = getattr(msg, key)
            except:
                continue

    def is_complete(self):
        if len(self.information['satellites']) > 0 and len(self.information['fix']) > 0 and len(self.information['track_and_speed']) and len(self.information['dop']) > 0 and len(self.information['transit_data']) > 0 and self.locked:
            return True
        else:
            return False

    def get_base_information(self):
        i = copy.deepcopy(self.information)

        minimal = {}
        try:
            minimal['t'] = get_epoch_time(
                i["fix"]["timestamp"], i["transit_data"]["datestamp"])
            minimal['lon'] = convert_lat_long(
                i["fix"]["lat"], i["fix"]["lat_dir"])
            minimal['lat'] = convert_lat_long(
                i["fix"]["lon"], i["fix"]["lon_dir"])

            minimal['s'] = i["transit_data"]["spd_over_grnd"]
            minimal['c'] = i["transit_data"]["true_course"]
            minimal['a'] = i["fix"]["altitude"]
        except Exception as e:
            print(e)
            pass

        self.reset()
        return minimal, i
