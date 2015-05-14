#!/usr/bin/python

import glob,json,sys

def mergeDevices(devList, newDev):
  for dev in devList:
    if dev['props']['device_id'] == newDev['props']['device_id']:
      # get a dict of obj.name, obj of the existing objects
      objDict = {}
      for obj in dev['objs']:
        if obj['name'] in objDict:
          print 'Duplicate in original list. quitting.'
          sys.exit(1)
        else:
          objDict[obj['name']] = obj
      # now add to the objDict.
      for obj in newDev['objs']:
        if obj['name'] in objDict:
          # name conflict. Append the intstance number at the end of the name.
          oldObj = objDict[obj['name']]
          if oldObj['props']['instance'] == obj['props']['instance']:
            print 'Duplicate found, pass'
            continue
          else:
            obj['name'] = obj['name'] + '_' + str(obj['props']['instance'])
        objDict[obj['name']] = obj
      dev['objs'] = objDict.values()
      dev['desc'] = dev['desc'] + ';' + newDev['desc']
      return
  # not found. add new device to the list.
  devList.append(newDev)


searchStr = sys.argv[1]

a = sys.argv[1:]

macDict = {}
for fn in a:
  f = open(fn)
  data = json.load(f)
  f.close()
  print '--->', fn
  for d in data:
    mac = '.'.join(str(x) for x in d['props']['mac'])
    if mac not in macDict.keys():
      macDict[mac] = []
    # macDict[mac].append(d)
    mergeDevices(macDict[mac], d)
    # print '--------->', len(macDict[mac])
   
for m in macDict:
  print m, len(macDict[m])
  totalObjs = 0
  for d in macDict[m]:
    totalObjs += len(d['objs'])
  fn = 'mac-' + m + '_devs-' + str(len(macDict[m])) + '_pts-' + str(totalObjs) + '.json'
  with open(fn, 'w') as outfile:
    json.dump(macDict[m], outfile, indent = 2, ensure_ascii=False)
  print 'Write to', fn


