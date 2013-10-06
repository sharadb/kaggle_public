import sys
import csv
import math
import numpy as np
from datetime import datetime
from collections import defaultdict

GROUP_SIZE = 300
SAMPLING_FREQUENCY_INDEX = 1
MEAN_INDEX = 0
STD_INDEX = 1
MIN_INDEX = 2
MAX_INDEX = 3
CORR_INDEX = 4
SQUARED_INDEX = 5
PRODUCT_INDEX = 6

class Triple(object):
  def __init__(self):
    self.x = []
    self.y = []
    self.z = []
    self.min_x = 1e9
    self.min_y = 1e9
    self.min_z = 1e9
    self.max_x = -1e9
    self.max_y = -1e9
    self.max_z = -1e9

  def add(self, x, y, z):
    self.x.append(x)
    self.y.append(y)
    self.z.append(z)
    self.min_x = min(self.min_x, x)
    self.min_y = min(self.min_y, y)
    self.min_z = min(self.min_z, z)
    self.max_x = max(self.max_x, x)
    self.max_y = max(self.max_y, y)
    self.max_z = max(self.max_z, z)

  def average(self):
    return [sum(self.x) / (len(self.x) + 0.),
            sum(self.y) / (len(self.y) + 0.),
            sum(self.z) / (len(self.z) + 0.)]

  def std(self):
    return [np.std(self.x),
            np.std(self.y),
            np.std(self.z)]

  def max(self):
    return [self.max_x, self.max_y, self.max_z]

  def min(self):
    return [self.min_x, self.min_y, self.min_z]

  def corr(self):
    correlation = np.corrcoef([self.x, self.y, self.z])
    values = [correlation[0][1], correlation[0][2], correlation[1,2]]
    return [x if not math.isnan(x) else 0 for x in values]

  def squared(self):
    return [sum([x*x for x in self.x]) / (len(self.x) + 0.),
            sum([y*y for y in self.y]) / (len(self.y) + 0.),
            sum([z*z for z in self.z]) / (len(self.z) + 0.)]

  def products(self):
    return [np.dot(self.x, self.y) / (len(self.x) + 0.),
            np.dot(self.y, self.z) / (len(self.y) + 0.),
            np.dot(self.x, self.z) / (len(self.z) + 0.)]


def GetStats(data):
  median = np.median(data)

  filtered_data = [x for x in data if x >= (1/4.) * median and x <= 4 * median]

  #mean = sum(filtered_data) / (len(filtered_data) + 0.0))
  return np.mean(filtered_data)

def GetSamplingFrequency(data):
  time_diff = []
  for i in range(1, len(data)):
    time_diff.append(data[i][0] - data[i-1][0])
  ret = GetStats(time_diff)
  if not math.isnan(ret):
    return ret
  return 0

def ComputeFeatures(f, data):
  if len(data) == 0:
    return
  bins = defaultdict(Triple)
  for row in data:
    bins[GetHour(row[0])].add(row[1], row[2], row[3])
  # assume f is already opened
  label = data[0][4]
  single_features = []
  single_features.append('%d:%f' % (SAMPLING_FREQUENCY_INDEX, GetSamplingFrequency(data)))

  for k in sorted(bins):
    stats = {}
    stats[MEAN_INDEX] = bins[k].average()
    stats[STD_INDEX] = bins[k].std()
    stats[MAX_INDEX] = bins[k].max()
    stats[MIN_INDEX] = bins[k].min()
    stats[CORR_INDEX] = bins[k].corr()
    stats[SQUARED_INDEX] = bins[k].squared()
    stats[PRODUCT_INDEX] = bins[k].products()
    for feature_index in stats:
      for val_index in xrange(len(stats[feature_index])):
        single_features.append('%d:%f' % (k * 21 + feature_index * 3 + val_index + 2, stats[feature_index][val_index]))
  print >>f, '%d %s' % (label, ' '.join(single_features))

def GetMinute(timestamp):
  dt = datetime.fromtimestamp(timestamp/1000)
  minute = dt.hour * 60 + dt.minute
  return int(minute/15)


def GetHour(timestamp):
  dt = datetime.fromtimestamp(timestamp/1000)
  return dt.hour

def main():
  input_file = sys.argv[1]
  output_file = sys.argv[2]

  reader = csv.reader( open( input_file ))
  writer = open(output_file, 'w')

  # skip headers
  reader.next()

  prev_device = 0		# device id
  n = 0

  data = []

  for line in reader:
    device = line[4]

    try:
      if device == prev_device:  # adding data to current group
        data.append([int(line[0]), float(line[1]), float(line[2]), float(line[3]), int(line[4])])
        if len(data) == GROUP_SIZE:
          ComputeFeatures(writer, data)
          data = []
      else:  # new group has started
        if prev_device != 0:
          ComputeFeatures(writer, data)
          data = []
          data.append([int(line[0]), float(line[1]), float(line[2]), float(line[3]), int(line[4])])
    except ValueError:
      print 'unexpected format in line %d' % n
      continue

    prev_device = device
    
    n += 1
    if n % 100000 == 0:
      print n

  # last device		
  ComputeFeatures(writer, data)
  writer.close()

if __name__ == '__main__':
  main()
