from math import sin, cos, sqrt, atan2, radians

class UpdateMonitor():
    '''This needs to notice when parked and the wake-up after it starts moving again'''
    
    def __init__(self, _sampling_distance = 200):
        self.planet_radius = 6373000
        self.prev_lat = 1000
        self.prev_lon = 1000
        
        self.sampling_distance = _sampling_distance
        self.cum_delta = 0
        
        self.wait = False
        self.pause_distance = 0.5
        self.resume_distance = 2
        
        self.indexer = 0
        self.moving_average_length = 10
        self.last_n_points = []
        
        self.accepted_callback = None
        
        self.num = 0
        
    def _distance_from_last(self, lat, lon):
        next_lat = radians(lat)
        next_lon = radians(lon)

        dlon = next_lat - self.prev_lat
        dlat = next_lon - self.prev_lon

        a = sin(dlat / 2)**2 + cos(next_lat) * cos(self.prev_lat) * sin(dlon / 2)**2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))

        self.prev_lat = next_lat
        self.prev_lon = next_lon

        return self.planet_radius * c
    
    def _calc_average(self):
        return float(sum(self.last_n_points)) / max(len(self.last_n_points), 1)
    
    def _recalc_average(self, delta):
        if len(self.last_n_points) < self.moving_average_length:
            self.last_n_points.append(delta)
            self.indexer = len(self.last_n_points) - 1
        else:
            self.indexer = (self.indexer % self.moving_average_length)
            self.last_n_points[self.indexer] = delta
            self.indexer += 1
        
        return self._calc_average()
    
    def process(self, _point):
        delta = self._distance_from_last(_point['lat'], _point['lon'])

        self.cum_delta += delta
        
        avg = self._recalc_average(delta)
    
        if avg < self.pause_distance and not self.wait:
            self.accepted_callback(_point)
            self.wait = True
        elif avg > self.resume_distance and self.wait:
            self.accepted_callback(_point)
            self.wait = False
            self.cum_delta = 0
        elif self.cum_delta > self.sampling_distance and not self.wait:
            self.accepted_callback(_point)
            self.cum_delta = 0