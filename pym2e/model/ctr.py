

class SaturatingCounter(object):
    def __init__(self, max_depth_t=1, max_depth_nt=1, 
                 initial_direction=False, initial_depth=0):
        self.max_depth_t  = max_depth_t
        self.max_depth_nt = max_depth_nt
        self.prediction   = initial_direction
        self.hysteresis   = initial_depth

    def predict(self):
        return self.prediction

    def update(self, outcome: bool):
        if (outcome != self.prediction):
            if self.hysteresis == 0:
                self.prediction = not self.prediction
            else:
                self.hysteresis -= 1
        else:
            if self.prediction == True:
                if self.hysteresis < self.max_depth_t:
                    self.hysteresis += 1
            else:
                if self.hysteresis < self.max_depth_nt:
                    self.hysteresis += 1





