import csv
import simplejson

import numpy as np

from nupic.data.file_record_stream import FileRecordStream
from htmresearch.frameworks.classification.classification_network import (
  configureNetwork, classifyNextRecord, setNetworkLearningMode,
  _getClassifierInference)

import nupic
from htmresearch.regions.CustomRecordSensor import CustomRecordSensor


_NUM_CATEGORIES = 2
_NUM_RECORDS = 4730
_DATA_DIR = "backup"
_CHANNEL = "attention"

_INPUT_FILES = ["%s/training-data-%s-%s.csv" % (_DATA_DIR, i, _CHANNEL)
                for i in range(_NUM_CATEGORIES)]

_CONFIG_JSON = "config/sensor_data_network_config.json"

_CONFIG = simplejson.load(open(_CONFIG_JSON, "rb"))

_REGION_CONFIG_KEYS = ("spRegionConfig", "tmRegionConfig",
                       "tpRegionConfig",
                       "classifierRegionConfig")

_REGION_NAMES = []
for region in _REGION_CONFIG_KEYS:
  if _CONFIG[region].get("regionEnabled"):
    _REGION_NAMES.append(_CONFIG[region]["regionName"])

def getNupicRegions(network):
  sensorRegion = None
  classifierRegion = None
  for region in network.regions.values():
    regionInstance = region
    print type(regionInstance.getSelf())
    if type(regionInstance.getSelf()) is CustomRecordSensor:
      sensorRegion = regionInstance.getSelf()
    elif type(regionInstance.getSelf()) is nupic.regions.CLAClassifierRegion.CLAClassifierRegion:
      classifierRegion = regionInstance.getSelf()

  return sensorRegion, classifierRegion

if __name__ == "__main__":
  dataSource = FileRecordStream(streamID="backup/training-data-attention.csv")
  network = configureNetwork(dataSource, _CONFIG)
  setNetworkLearningMode(network, _REGION_NAMES, True)


  sensorRegion = network.regions[
  _CONFIG["sensorRegionConfig"].get("regionName")]
  classifierRegion = network.regions[
  _CONFIG["classifierRegionConfig"].get("regionName")]

  # num_correct = 0.0
  # for row_id in range(_NUM_RECORDS * _NUM_CATEGORIES):
  #   network.run(1)
  #   actualValue = sensorRegion.getOutputData("categoryOut")[0]
  #   inferredCategory = _getClassifierInference(classifierRegion)
  #
  #   if int(inferredCategory) == int(actualValue):
  #     num_correct += 1

  sensorRegion, classifierRegion = getNupicRegions(network)
  # check whether learning is on for classifier
  print " Learning for classifierRegion: ", classifierRegion.learningMode
  classifierRegion.learningMode = True

  headers = ["x", "y", "label"]
  readers = {category: None for category in range(_NUM_CATEGORIES)}
  for category in range(_NUM_CATEGORIES):
    csvFile = open(_INPUT_FILES[category], "rb")
    reader = csv.reader(csvFile)
    # skip 3 header rows
    reader.next()
    reader.next()
    reader.next()
    readers[category] = reader

  num_correct = 0.0
  for row_id in range(_NUM_RECORDS):

    # alternate categories
    for category in range(_NUM_CATEGORIES):
      row = readers[category].next()
      data = dict(zip(headers, row))
      x = int(data["x"]) / 1000000 # s
      y = float(data["y"])
      label = int(category)
      classificationResults = classifyNextRecord(network,
                                                 _CONFIG,
                                                 x,
                                                 y,
                                                 label)
      inferredCategory = classificationResults["bestInference"]

      print "Timestamp: %s, Data: %d " % (x, y)
      print "Actual: %s | Predicted: %s " % (category,
                                             inferredCategory)
      if int(inferredCategory) == int(category):
        num_correct += 1

  print "ACCURACY: %s " % (num_correct / (_NUM_RECORDS * _NUM_CATEGORIES))

  setNetworkLearningMode(network, _REGION_NAMES, False)
  network.save("motor_imagery.nta")
  #
  #
  # sensorRegion, classifierRegion = getNupicRegions(network)
  #
  # sensorInput = None
  # sensorOutput = {'categoryOut': np.array([0]),
  #                 'resetOut': [None],
  #                 'sourceOut': [],
  #                 'sequenceIdOut': [None],
  #                 'encodingOut': None,
  #                 'dataOut': np.zeros((sensorRegion.encoder.width, ))}
  # sensorRegion.compute(sensorInput, sensorOutput)
  #
  #
  # classifierRegion._claClassifier._patternNZHistory