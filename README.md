#Deploying

To build a new cluster simply
run deploy.sh
i.e.
```
./deploy.sh
```

#Destroying

To destroy an environment run destroy.sh
i.e.
```
./destroy.sh
```

*NB* On Destroy it may fail due to EBS volumes being atached. Log in to AWS console, stop the instances and then re-run

