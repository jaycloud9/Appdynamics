#!/bin/bash

source cluster-hosts.env

pub_key="ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCjMgFemM78/QbVcNiQoHfv3VK6tE6im/fqf8s+WrVzh8B8tMiDUJzV+aqAZxqO1tikidPozDhcRSHdcR/HJrvUpWYL7TbnLb7Lvu9cINqIGvlNF3xA8Ve3LTglV0mT8LsT4z/ZfDwSr834WkZWF9TDuh1O2gnd4G6X5+LWrDnLJExnv8mTz7fhqWdXHyzSa5ARLc1pUd2RyhfEA7MMRZhgox1LwRsRYJJrbbIaaQ/6GCuq9j3yQ2X+Vjt2ldb7d/mzMwck643KYNIRvsp4w4462JWT5MYbA8VxhGTS2IkB4ZsXmjEjYu4thZ/3radZLdvL+i+lb6GFuAa0sneJe4cP matthew@Matthews-MacBook.local\nssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDIKA0orx/rL5D6TMg4jcem4m6MZzrlbdESPE9T55EAt10XnyqXxQ2xy0NIA+MWLKx5kaJnz1R2xSp82O18cg5t0yp8Se1MrCO0l8USRo02r79xJN4lmuFX1+0s6fvRZQLJ2dMfv0s8ABbRxHF13oQoK3FHCPVFGBOed98Bk5DJiiseZx0oa9OsN5Ooi9OH2MsIo9jEw6gynyABB0g52DisRxEEao3FsnFCKNXDzbVvMa2hOT78k6BHI681Le5ZskaAOqwn9P+pKg7M65VDsD4Tew2e3mpKj2uL7wvhMwX1syq1jMJu8h/GVqfg1OTwau/NyTS097/47tGef0vsIvKD ose@01masterdoserh"

for host in $ALL_HOSTS; do

ssh $host "echo $pub_key > ~/.ssh/authorized_keys"


done
