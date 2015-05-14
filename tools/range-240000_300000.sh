#!/bin/bash
R1=240000
MAX=300000
DELTA=1000
while [  $R1 -lt $MAX ]; do
   let R2=R1+DELTA-1
   echo ./bacnet-scan-range -i eth1 -r $R1-$R2 scan_range/range_$R1-$R2.json
   ./bacnet-scan-range -i eth1 -r $R1-$R2 scan_range/range_$R1-$R2.json

   let R1=R1+DELTA
done
