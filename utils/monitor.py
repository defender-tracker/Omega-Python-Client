import logging
from math import sin, cos, sqrt, atan2, radians

from utils.error_handling import error_message


class UpdateMonitor():
    '''This needs to notice when parked and the wake-up after it starts moving again'''

    def __init__(self, sampling_distance=200, pause_distance=0.5, resume_distance=2, moving_average_length=10, update_callback=None):

        self._reset()

        self._sampling_distance = sampling_distance
        self._update_callback = update_callback
        self._pause_distance = pause_distance
        self._resume_distance = resume_distance
        self._moving_average_length = moving_average_length

    def set_sampling_distance(self, distance):
        self._sampling_distance = distance

    def set_pause_distance(self, distance):
        self._pause_distance = distance

    def set_resume_distance(self, distance):
        self._resume_distance = distance

    def set_moving_average_length(self, length):
        self._moving_average_length = length

    def _reset(self):
        self._planet_radius = 6373000

        self._prev_lat = 1000
        self._prev_lon = 1000

        self._cum_delta = 0
        self._wait = False

        self._indexer = 0
        self._last_n_points = []

    def _distance_from_last(self, lat, lon):
        next_lat = radians(lat)
        next_lon = radians(lon)

        dlon = next_lat - self._prev_lat
        dlat = next_lon - self._prev_lon

        a = sin(dlat / 2)**2 + cos(next_lat) * \
            cos(self._prev_lat) * sin(dlon / 2)**2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))

        self._prev_lat = next_lat
        self._prev_lon = next_lon

        return self._planet_radius * c

    def _calc_average(self):
        return float(sum(self._last_n_points)) / max(len(self._last_n_points), 1)

    def _recalc_average(self, delta):
        if len(self._last_n_points) < self._moving_average_length:
            self._last_n_points.append(delta)
            self._indexer = len(self._last_n_points) - 1
        else:
            self._indexer = (self._indexer % self._moving_average_length)
            self._last_n_points[self._indexer] = delta
            self._indexer += 1

        return self._calc_average()

    def process(self, _point):
        try:
            delta = self._distance_from_last(_point['lat'], _point['lon'])

            self._cum_delta += delta

            avg = self._recalc_average(delta)

            if avg < self._pause_distance and not self._wait:
                logging.debug("Monitor - Pause")
                self._update_callback(_point)
                self._wait = True
            elif avg > self._resume_distance and self._wait:
                logging.debug("Monitor - Resume")
                self._update_callback(_point)
                self._wait = False
                self._cum_delta = 0
            elif self._cum_delta > self._sampling_distance and not self._wait:
                logging.debug("Monitor - Normal")
                self._update_callback(_point)
                self._cum_delta = 0

        except Exception as e:
            logging.error(error_message(e))
