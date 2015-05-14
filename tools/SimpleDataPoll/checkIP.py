#!/usr/bin/python

import glob,json,sys

searchStr = sys.argv[1]

#a = glob.glob(searchStr)
#print a, searchStr
a = sys.argv[1:]

macList = []
for fn in a:
  f = open(fn)
  data = json.load(f)
  f.close()
  localMac = []
  objCnt = 0
  print '--->', fn
  for d in data:
    if d['props']['mac'] not in macList:
      macList.append(d['props']['mac'])
      #print fn, d['props']['device_id'], d['props']['mac']
    if d['props']['mac'] not in localMac:
      localMac.append(d['props']['mac'])
    objCnt += len(d['objs'])
  for m in localMac:
    print m
  print objCnt, 'objects.'

