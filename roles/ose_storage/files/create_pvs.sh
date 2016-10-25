#!/bin/bash
sizes=(512Mi 1Gi 2Gi)
si=0
rc=0
for vol in $(seq 1 20)
do
	size=${sizes[$si]}
	pv=pv$vol
	sed s/%pv/$pv/g /tmp/pv-template.yaml | sed s/%size/$size/g | oc create -f -
  rc=$?
	si=$(($si+1))
	[[ $si -ge 3 ]] && si=0
done
exit $rc
