#Setup
To setup a new subscription you will need to follow the following document:
1. https://docs.microsoft.com/en-us/azure/azure-resource-manager/resource-group-create-service-principal-portal
2. Then update the config file with the correct details.
3. Set up a subdomain. Create a ```mp_sub_core```  where sub is descriptive such as Dev or prod or test (environment) resource group
4. Inside that resource group create a DNS zone called ```sub.temenos.cloud```
5. In the root zone (temenos.cloud) as a NS record with the sub name and the NS servers from the new dns zone that you created

#Azure RM inventory
The azure_rm inventory will need to be created and the credential file in ~/.azure/crednetials will need updating


#Deploying

To build a new cluster simply
run deploy.sh
i.e.
```
./deploy.sh azure cluster1
```

#Destroying

To destroy an environment run destroy.sh
i.e.
```
./destroy.sh azure cluster1
```

#FYI
This repo is now built upon every commit...
