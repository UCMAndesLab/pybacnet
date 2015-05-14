#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  SimpleDataPoll.py
#  Simple data polling based on the input json file.
#  #  Copyright 2014 Tao Liu <tliu@andes.ucmerced.edu> #  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or #  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  
#  

import json, requests, time, logging, sys, argparse, uuid
import signal
import threading
import random

from pybacnet import bacnet

# Shared data buffer.
dataBuf = list()

# Conditional variable.
bufFull = threading.Condition()
pollingTimer = threading.Event();
bacnetResource = threading.Condition();
exitingLock = threading.Condition();

# Max buffer size before report to the archiver.
MAX_BUFFER_SIZE = 100

# How often we are sampling
SAMPLING_RATE = 30 
TIMEOUT_DELAY = 0.5
BACNET_IFACE = 'eth1'
BACNET_PORT = '47900'
REPORT_SOURCE_NAME = 'University of California, Merced'
API_KEY="dS3M60wYY8e4hbDK2I3TZzhMTd0MVDBeKsG3";
REPORT_URL = "http://169.236.151.104:8079/add/{0}".format(API_KEY)

# Shared varible for exiting
isExiting = False 

DEBUG_FORMAT = '[ %(levelname)s ] [%(asctime)-15s %(threadName)-6s ] %(message)s'
logging.basicConfig(filename='simple_poll.log',level=logging.DEBUG, format=DEBUG_FORMAT)

def signal_handler(signal, frame):
  global isExiting;
  print('Graceful shutdown....');
  logging.warning('Graceful shutdown....')
  isExiting = True

  pollingTimer.set();


  bufFull.acquire();
  bufFull.notify()
  bufFull.release();

  safeExit();

def safeExit():
   if isExiting == True:
      t = threading.current_thread();
      logging.warning('Killing Thread {0}.'.format(t.name) );
      sys.exit(0);

def pollData(srcList):
  backOff = 1;
  randBackoff = 0;
  global isExiting; 
  while not isExiting:
    for s in srcList:
      val = None
      bacnetResource.acquire();
      try:
        print s[1]
        print s[2]
        print s[3]

        val = bacnet.read_prop(s[1], s[2], s[3], bacnet.PROP_PRESENT_VALUE, -1)
        #print("{0}+{1}+{2}".format(s[1], s[2], s[3]))
      except IOError as err:
        logging.warning(err)
        backOff = 2*backOff;
      except Exception as err:
        logging.warning(err)
        backOff = 2*backOff;
      finally:
        bacnetResource.release();

      if val is not None:
        logging.debug("Value: {0}".format(val));
        # Successful poll, decrement backoff
        if(backOff > 1):
           backOff = backOff - 0.01;

        ts = int(time.time() * 1000)
        bufFull.acquire()
        dataBuf.append( (s[0], [ts, val]) )
        if len(dataBuf) >= MAX_BUFFER_SIZE:
          # Notify the reporter
          bufFull.notify()
        bufFull.release()
      else:
         logging.debug("No value reported");

      randBackoff = random.randint(0, round(backOff)) + SAMPLING_RATE;
      pollingTimer.wait(randBackoff)
      safeExit();

    logging.info('Polled Data')

def reportData(metadata):
  reportHeaders = {'content-type': 'application/json'}
  lastTS = time.time()
  while not isExiting:
    bufFull.acquire()
    while len(dataBuf) < MAX_BUFFER_SIZE:
      bufFull.wait()
      safeExit();

    # Copy the data buffer for reporting.
    data = list(dataBuf)
    del dataBuf[:]
    bufFull.release()

    jsonData = dict()
    for record in data:
      uid = record[0]
      # print metadata[uid]['path'], record[1]
      jsonChunk = createReportJSON(uid, REPORT_SOURCE_NAME, metadata[uid], record[1])
      #print '---'
      #print json.dumps(jsonChunk)
      if jsonChunk: jsonData[metadata[uid]['path']] = jsonChunk
    print 'Reporting', len(jsonData), 'entries'

    # report to archiver
    r = requests.post(REPORT_URL, data=json.dumps(jsonData), headers=reportHeaders)
    if r.ok:
      logging.info("Report to the backend.")
      print 'Report OK. Interval (sec):', time.time() - lastTS
    else:
      logging.info("Report failed.")
      print 'Report failed.  Interval (sec):', time.time() - lastTS, r
    lastTS = time.time()
    safeExit();

def createReportJSON(uid, sourcename, mdata, reading):
  #  sampleReport = """
  # "/COB/UCM Core Buildings/UCM Core Buildings/Classroom and Office Building: 0202/HVAC: 0202/First Floor/DDV-101 RM-116/CD Static Request": {
  #  "Properties": {
  #  "Timezone": "America/Los_Angeles",
  #  "UnitofMeasure": "Reserved for Use by ASHRAE",
  #  "ReadingType": "double"
  #  },
  #  "Metadata": {
  #    "SourceName": "UCM_ALL_BUILDING_TEST1"
  #  },
  #  "uuid": "11b9c6f6-69bc-5d5c-9615-ecc69d4932b3",
  #  "Readings": "[[1412970469000, 0.0]]"
  #}
  #"""
  res = {'Properties': {'Timezone': 'America/Los_Angeles', 'UnitofMeasure': str(mdata['unit']), "ReadingType": "double"}}
  res['Metadata'] = {'SourceName': sourcename}
  res['uuid'] = uid
  res['Readings'] = [reading]
  return res

def parseSource(srcJson, namespace):
  srcList = list()
  metadata = dict()
  for dev in srcJson:
    devProp = dev['props']
    objs = dev['objs']
    for obj in objs:
      objPath = str(obj['desc'] + '/' + obj['name'].replace('/', '_'))

      # Small hack to reduce the path length.
      objPath = objPath.replace('/UCM Core Buildings/UCM Core Buildings/','/')
      objPath = objPath.replace('/UCM Science Buildings/', '/')
      
      uid = str(uuid.uuid5(namespace, objPath))
      if uid in metadata:
        print "Error: duplicate point definition:", objPath
        sys.exit(1)
      else:
        metadata[uid] = {"path": objPath, "unit": obj['unit'], 'name': obj['name'], 'data_type': obj['data_type']}
        srcList.append( (uid, dev['props'], obj['props']['type'], obj['props']['instance']) )
  return (srcList, metadata)
      


def main(jsonFile):
  signal.signal(signal.SIGINT, signal_handler)

  print "Opening JSON file", jsonFile
  with open(jsonFile) as f:
    srcJson = json.load(f)

  if srcJson:
    logging.info('Done. %d read.'.format(len(srcJson)) )
    for dev in srcJson:
      MACStr = ".".join(map(str, dev['props']['mac']));
      logging.info( 'Device MAC:{0} Objs: {1}'.format(MACStr , len(dev['objs']) ))

  # Some constants, should get them from the sMAP configuration file.
  namespace = uuid.UUID('{0262cfc4-5585-11e4-9e35-164230d1df67}')

  # generate source point list.
  (srcList, metadata) = parseSource(srcJson, namespace)
  uniqueSrc = dict();

  for entry in srcList:
      k = "{0}_{1}".format(".".join(map(str, entry[1]['mac'])), entry[1]['device_id']);
      if not uniqueSrc.has_key(k):
         uniqueSrc[k] = list();
      uniqueSrc[k].append(entry);
  

  # Init bacnet
  bacnet.Init(BACNET_IFACE, BACNET_PORT)

  numOfThreads = 0;
  for key in uniqueSrc:
      threadName = 'Data{0}'.format(numOfThreads);
      logging.info("Starting Thread:{0}".format(threadName))
      pro = threading.Thread(name=threadName, target = pollData, args= (uniqueSrc[key],) )
      pro.start()
      numOfThreads = numOfThreads + 1;
      

  threadName = 'Report';
  con = threading.Thread(name=threadName, target = reportData, args = (metadata,) )
  logging.info("Starting Thread: {0}".format(threadName))
  con.start()
  
  while(True):
     signal.pause();

if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument("jsonFile", help="Path to the BACNet source defination (JSON).")
  parser.add_argument("initPort", help='Port to init the BACNet. Should be different.')
  args = parser.parse_args()
  BACNET_PORT = args.initPort
  r = main(args.jsonFile)
