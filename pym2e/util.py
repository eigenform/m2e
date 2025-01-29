
import itertools

def grouper(iterable, n, *, incomplete='fill', fillvalue=None):
    "Collect data into non-overlapping fixed-length chunks or blocks"
    # grouper('ABCDEFG', 3, fillvalue='x') --> ABC DEF Gxx
    # grouper('ABCDEFG', 3, incomplete='strict') --> ABC DEF ValueError
    # grouper('ABCDEFG', 3, incomplete='ignore') --> ABC DEF
    args = [iter(iterable)] * n
    if incomplete == 'fill':
        return itertools.zip_longest(*args, fillvalue=fillvalue)
    if incomplete == 'strict':
        return zip(*args, strict=True)
    if incomplete == 'ignore':
        return zip(*args)
    else:
        raise ValueError('Expected fill, strict, or ignore')

def print_samples_history(samples, col=64):
    for vals in grouper(samples, col, incomplete='fill', fillvalue=None):
        s = ''.join('x' if x == None else "{}".format(x) for x in vals)
        print(s, flush=True)

def print_samples_history_wide(samples, col=64, fmtstr="{:3}"):
    for vals in grouper(samples, col, incomplete='fill', fillvalue=None):
        s = ''.join('xxx ' if x == None else fmtstr.format(x) for x in vals)
        print(s, flush=True)


def samples_to_dist(samples):
    """ Count the different observed values in a set of samples """
    dist = {}
    for val in samples:
        if dist.get(val) == None:
            dist[val] = 1
        else:
            dist[val] += 1
    return sorted(dist.items())

class PatternCounter(object):
    """ Manually specify a pattern of branch outcomes """
    def __init__(self, pattern):
        self.pattern = pattern
        self.ctr = 0

    def output(self):
        return self.pattern[self.ctr]
    def output_bool(self):
        return True if self.pattern[self.ctr] == 1 else False

    def next(self):
        self.ctr += 1
        if self.ctr == len(self.pattern):
            self.ctr = 0

class SingleCounter(object):
    """ Simulates a single periodic change in the branch outcome """
    def __init__(self, period, initial=0):
        self.initial = initial
        self.period = period
        self.ctr = 1
        self.value = 0

    def output(self):
        return self.value
    def output_bool(self):
        return True if self.value == 1 else False


    def next(self):
        if self.ctr == (self.period - 1):
            self.ctr = 0
            self.value = self.initial ^ 1
        else:
            self.value = self.initial
            self.ctr += 1

class FlipCounter(object):
    """ Simulates a periodic flip in the branch outcome """
    def __init__(self, period, initial_value=0):
        self.period = period
        self.ctr = 1
        self.value = initial_value

    def output(self):
        return self.value
    def output_bool(self):
        return True if self.value == 1 else False

    def next(self):
        if self.ctr == self.period:
            self.value = self.value ^ 1
            self.ctr = 0
        self.ctr += 1


