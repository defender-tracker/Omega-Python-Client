import logging
from math import sin, cos, sqrt, atan2, radians, sqrt
from statistics import stdev

import shelve

from utils.error_handling import error_message

class Sampler():
    
    def __init__(
        self,
        minimum_sampling_distance=50,
        maximum_sampling_distance=30000,
        x_max=0.15,
        pause_distance=0.5,
        resume_distance=5,
        moving_average_length=20,
        update_callback=None
        ):

        self.__reset()
        
        self._history = shelve.open(
            'sampler_history'
        )

        self._maximum_sampling_distance = maximum_sampling_distance
        self._minimum_sampling_distance = minimum_sampling_distance
        self._x_max = x_max
        
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

    def __reset(self):
        self._planet_radius = 6373000

        self._prev = {
            'latitude': 1000,
            'longitude': 1000
        }
        self._last_update = self._prev
        self._last_n_points = [self._prev]

        self._wait = False
        
    def __distance_from_last_update(self, _point):
        return self.__distance_between_points(_point, self._last_update)
    
    def __distance_from_prev(self, _point):
        delta = self.__distance_between_points(_point, self._prev)
        self._prev = _point
        return delta
        
    def __distance_between_points(self, _next, _prev):
        next_lat = radians(_next.get('latitude'))
        next_lon = radians(_next.get('longitude'))
        
        prev_lat = radians(_prev.get('latitude'))
        prev_lon = radians(_prev.get('longitude'))

        dlon = next_lat - prev_lat
        dlat = next_lon - prev_lon

        a = sin(dlat / 2)**2 + cos(next_lat) * \
            cos(prev_lat) * sin(dlon / 2)**2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))

        return self._planet_radius * c
    
    def __dynamic_sampling_function(self, x):
        minimum = self._minimum_sampling_distance
        maximum = self._maximum_sampling_distance
        x_max = self._x_max
        return (minimum*x_max)/(x + ((x_max*minimum)/maximum))

    def __calc_averages(self):
        
        sums = {
            'distance_change': 0,
            'speed': 0,
            'cyclical_course': 0
        }
        
        for key in list(self._history.keys()):
            sums['distance_change'] += self._history.get(key).get('distance_change')
            sums['speed'] += self._history.get(key).get('speed')
            sums['cyclical_course'] += self._history.get(key).get('cyclical_course')
            
        return {key: sums.get(key)/max(len(self._history.keys()), 1) for key in sums.keys()}
    
    def __calc_deviations(self):
        
        if len(self._history.keys()) > 1:
            sums = {
                'distance_change': [],
                'speed': [],
                'cyclical_course': []
            }

            for key in list(self._history.keys()):
                sums['distance_change'].append(self._history.get(key).get('distance_change'))
                sums['speed'].append(self._history.get(key).get('speed'))
                sums['cyclical_course'].append(self._history.get(key).get('cyclical_course'))

            return { key: stdev(sums.get(key)) for key in sums.keys() }
        else:
            return {
                'distance_change': 0,
                'speed': 0,
                'cyclical_course': 0
            }
        
    def __history_append(self, _update):
        
        if len(self._history) < self._moving_average_length:
            self._history[str(_update.get('timestamp'))] = _update
        else:
            keys = list(self._history.keys())
            keys.sort(key=int)
            del(self._history[keys[0]])
            self._history[str(_update.get('timestamp'))] = _update
            
    def __call_callback(self, _update):
        
        self._last_update = _update
        
        latest_key = int(_update.get('timestamp'))
        
        keys = list(self._history.keys())
        keys.sort(key=int)
        
        for key in keys:
            if int(key) <= latest_key:
                del(self._history[str(key)])
                
        minimised = {
            't': _update.get('timestamp'),
            'lon': _update.get('longitude'),
            'lat': _update.get('latitude'),
            's': _update.get('speed'),
            'c': _update.get('course'),
            'a': _update.get('altitude')
        }
        
        self._update_callback(minimised)
        
    def __process_history(self, _ratio):
        _sampling_distance = self.__dynamic_sampling_function(_ratio)
                
        keys = list(self._history.keys())
        keys.sort(key=int)
        
        _historic_cum_delta = 0
        
        prev_historic_update = {}
        
        for key in keys:
            historic_update = self._history.get(key)
            
            if len(prev_historic_update) > 0:
                
                prev_delta = self.__distance_between_points(historic_update, prev_historic_update)
                
                _historic_cum_delta += prev_delta
                prev_historic_update = historic_update

                if _historic_cum_delta > _sampling_distance:
                    logging.debug("Monitor - Normal")
                    self.__call_callback(historic_update)
                    _historic_cum_delta = 0
 
            else:
                prev_historic_update = historic_update
                _historic_cum_delta = self.__distance_from_last_update(historic_update)

    def process_update(self, _update):
        
        try:
        
            if _update.get('status') != 'A':
                return
            
            _update['cyclical_course'] = (sin(radians(_update['course']))+1)/2
            _update['distance_change'] = self.__distance_from_prev(_update)

            self.__history_append(_update)

            _averages = self.__calc_averages()
            _deviations = self.__calc_deviations()

            if _averages.get('distance_change') < self._pause_distance and not self._wait:
                logging.debug("Monitor - Pause")
                self.__call_callback(_update)
                self._wait = True
            elif _averages.get('distance_change') > self._resume_distance and self._wait:
                logging.debug("Monitor - Resume")
                self.__call_callback(_update)
                self._wait = False
            elif not self._wait:
                _quotient = _deviations['cyclical_course']/(1 + sqrt(_averages['speed']))
                self.__process_history(_quotient)

        except Exception as e:
            logging.error(error_message(e))
