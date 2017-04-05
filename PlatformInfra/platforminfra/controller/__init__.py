"""PlatformInfra Controller."""

from platforminfra.templates import Template
from platforminfra.config import Config
from platforminfra.helpers import Response
from platforminfra.infrastructure.azure import Azure
from multiprocessing import Process, Queue, Lock

from ..helpers import Jenkins, Gitlab, Helpers
import re


class Controller(object):
    """Controls the platformInfra."""

    def __init__(self):
        """Initialise the controller."""
        self.templates = Template(templateDir='./templates/')
        self.tags = dict()
        self.subnets = list()
        self.vms = list()
        self.lbs = list()
        self.config = Config()

    def getTemplate(self, templateName):
        """Get a Template by Name."""
        return self.templates.loadTemplate(templateName)

    def setTags(self, data):
        """Return the tags element."""
        print("Creating Tags")
        self.tags = {**self.tags, **data}

    def checkUUIDInUse(self, uuid):
        """Given a UUID validate if it is in use or not."""
        provider = Azure(
            self.config.credentials['azure'],
            self.config.defaults['resource_group_name'],
            self.config.defaults['storage_account_name']
        )

        uuids = provider.getResources()
        if uuid in uuids:
            return True
        else:
            return False

    def getVMDetails(self, id, type):
        """Get a VM object back from an ID."""
        vm = dict()
        vm['id'] = id
        idSplit = re.split(r"/", id.strip())
        vm['name'] = idSplit[-1]
        vm['type'] = type
        countSplit = re.split(r"{}".format(type), vm['name'].strip())
        vm['position'] = countSplit[-1]

        return vm

    def getVMBEID(
            self, provider, id=None, template=None,
            server=None, uuid=None
            ):
        """For an ID get the BE ID."""
        beId = None
        if template and uuid and server:
            if 'load_balancers' in template['services']:
                for lb in template['services']['load_balancers']:
                    if lb['be_servers'] == server:
                        lbName = lb['name']
                resources = provider.getResources(id=uuid)
                for id in resources['ids']:
                    idSplit = re.split(r"/", id.strip())
                    resourceType = idSplit[6] + "/" + idSplit[7]
                    resourceName = idSplit[-1]
                    if resourceType == 'Microsoft.Network/loadBalancers' and \
                            lbName in resourceName:
                        print("Getting LB")
                        # Found the Id of the Load balancer for the server
                        lb = provider.getResourceById(resourceType, id)
                        beId = lb.properties['backendAddressPools'][0]['id']
        return beId

    def addVM(
            self, vms, provider, template, uuid, application,
            count=None, persistData=False
            ):
        """Given an Existing list of VMs Add more."""
        if not count:
            for server in template['services']['servers']:
                if server['name'] == vms[0]['type']:
                    count = server['count']
        vm = dict()
        vm['count'] = count
        print("Getting BE ID")
        beId = self.getVMBEID(
            provider,
            template=template,
            server=vms[0]['type'],
            uuid=uuid
        )
        if 'id' in vms[0]:
            existingIds = list()
            for item in vms:
                if provider.checkResourceExistById(
                    'Microsoft.Compute/virtualMachines',
                    item['id']
                ):
                    existingIds.append(item['id'])
            vm['existing'] = existingIds
        if beId:
            vm['beId'] = beId
        vm['name'] = vms[0]['type']
        vmList = [vm]
        # There's only a single subnet per network
        subnet = provider.getSubnetID(uuid + "0")
        self.tags['uuid'] = uuid
        self.subnets.append({'subnets': {uuid: subnet}})
        self.createVms(vmList, provider)

        jenkinsServer = Jenkins(
            self.config.credentials['jenkins']['url'],
            user=self.config.credentials['jenkins']['user'],
            password=self.config.credentials['jenkins']['password']
        )
        print("Running Jenkins Job")
        jenkinsServer.runBuildWithParams(
            application,
            params={
                "UUID": self.tags['uuid']
            }
        )

    def createNetworks(self, data, provider):
        """Create Networks."""
        # Must complete before everything else is built
        subNets = Queue()
        print("Creating network")
        netProcs = list()
        for idx, network in enumerate(data):
            netId = str(self.tags['uuid'])+str(idx)
            p = Process(
                target=provider.network,
                args=(network, netId, self.tags, subNets)
            )
            netProcs.append(p)
            p.start()

        subnets = dict()
        for proc in netProcs:
            proc.join()
            subnets['subnets'] = subNets.get()

        self.subnets.append(subnets)

    def createVms(self, data, provider, persistData=False):
        """Create VMs."""
        print("Creating Servers")
        vms = Queue()
        vmLock = Lock()
        # Processes that can be run in parrallel
        serverProcs = list()
        try:
            for i in self.subnets:
                if self.tags['uuid'] in i['subnets']:
                    vmSubnet = i['subnets'][self.tags['uuid']]
            for server in data:
                p = Process(
                    target=provider.virtualMachine,
                    args=(
                        server,
                        self.tags,
                        vmSubnet,
                        vms,
                        vmLock,
                        persistData
                    )
                )
                vmDetails = {
                    'servers': server['name'],
                    'thread': p
                }
                if 'dns' in server:
                    vmDetails['dns'] = server['dns']
                serverProcs.append(vmDetails)
                p.start()

            for proc in serverProcs:
                proc['thread'].join()
                tmpData = vms.get()
                if 'dns' in proc:
                    # Only apply to the first server
                    result = provider.addDNS(
                        tmpData['vms'][0]['public_ip'],
                        proc['dns'] + '-' + self.tags['uuid']
                    )
                    tmpData['dns'] = result
                self.vms.append(tmpData)
        except Exception as e:
            raise Exception(e)

    def createLoadBalancers(self, data, provider):
        """Create Load balancers."""
        print("Creating Load Balancers")
        for item in data:
            for lbName, details in item.items():
                if details['load_balancer']['health_protocol'] == 'Tcp' or \
                        details['load_balancer']['health_protocol'] == 'Http':
                    if details['load_balancer']['health_protocol'] == 'Http':
                        if 'health_path' not in details['load_balancer']:
                            e = {
                                'error': "Must specify health_path with Http"
                            }
                            raise Exception(e)

                    # Create LB here
                    print("Creating LB: {}".format(lbName))
                    lbData = provider.loadBalancer(
                        details['load_balancer'],
                        self.tags
                    )
                    # Create Vm's Here
                    details['servers']['beId'] = lbData['lbInfo'] \
                        .backend_address_pools[0].id
                    serverList = list()
                    serverList.append(details['servers'])
                    self.createVms(
                        serverList,
                        provider
                    )
                    record = self.tags['uuid']
                    if 'domain' in details['load_balancer']:
                        record = details['load_balancer']['domain'] + '-' + \
                            record
                    else:
                        record = details['load_balancer']['name'] + '-' + \
                            record

                    result = provider.addDNS(
                        lbData['publicIp'].ip_address,
                        record
                    )
                    self.lbs.append({
                        details['load_balancer']['name']: result
                    })
                else:
                    e = {
                        'error': "back_end_protocol must be 'Http' or 'Tcp'"
                    }
                    raise Exception(e)

    def createEnvironment(self, data):
        """Create an Environment."""
        template = self.templates.loadTemplate(
            data['infrastructureTemplateID']
        )

        if self.checkUUIDInUse(data['id']):
            rsp = Response({'error': 'UUID in use'})
            return rsp.httpResponse(404)
        response = list()
        self.tags['uuid'] = data['id']
        provider = Azure(
            self.config.credentials['azure'],
            self.config.defaults['resource_group_name'],
            self.config.defaults['storage_account_name'],
            template,
            data['id']
        )
        if 'error' in provider.credentials:
            rsp = Response(provider.credentials)
            return rsp.httpResponse(404)

        buildMap = {
            "servers": self.createVms,
            "networks": self.createNetworks,
            "load_balancers": self.createLoadBalancers,
            "tags": self.setTags
        }
        # Build core resources
        print("Creating RG")
        provider.createResourceGroup()
        print("Creating SA")
        provider.createStorageAccount()
        try:
            for resource in provider.resources['resources']:
                for k, v in resource.items():
                    if k in buildMap:
                        if k == 'tags':
                            buildMap[k](v)
                        else:
                            buildMap[k](v, provider)
                        continue
        except Exception as e:
            print("Something failed :'(")
            rsp = Response(e)
            return rsp.httpResponse(404)

        for vmRsp in self.vms:
            response.append(vmRsp)

        # By this point an environment should be created so Execute Jenkins job
        jenkinsServer = Jenkins(
            self.config.credentials['jenkins']['url'],
            user=self.config.credentials['jenkins']['user'],
            password=self.config.credentials['jenkins']['password']
        )
        print("Running Jenkins Job")
        jenkinsServer.runBuildWithParams(
            data["application"],
            params={
                "UUID": self.tags['uuid']
            }
        )
        print("Connecting to Gitlab")
        glServerConn = self.config.credentials['gitlab']['url']
        glServerToken = self.config.credentials['gitlab']['token']
        # When we know if theres more than one or not move to config.yml
        glSourceProject = "customer-demo"
        glSourceTeam = "root"
        glServer = Gitlab(glServerConn, glServerToken)
        glSourceProject = glServer.getProject(glSourceTeam, glSourceProject)

        print("Create user")
        user = glServer.createUser(
            self.tags['uuid'],
            self.tags['uuid'],
            Helpers.randStr(10),
            self.tags['uuid'] + '@example.net'
        )
        forked = glServer.forkProject(
            user.username,
            glSourceProject.id
        )
        response.append({'git_url': forked.web_url})
        response = response + self.lbs
        rsp = Response({'Resources': response})
        return rsp.httpResponse(200)

    def listEnvironments(self):
        """Return a list of environments."""
        provider = Azure(
            self.config.credentials['azure'],
            self.config.defaults['resource_group_name'],
            self.config.defaults['storage_account_name']
        )

        rsp = Response({
            "Environments": provider.getResources()
        })
        return rsp.httpResponse(200)

    def deleteEnvironment(self, data):
        """Delete a specific Environments Resources."""
        provider = Azure(
            self.config.credentials['azure'],
            self.config.defaults['resource_group_name'],
            self.config.defaults['storage_account_name']
        )
        print("Deleting Resources")
        deleteResources = {'Azure': provider.getResources(data['uuid'])}
        glServerConn = self.config.credentials['gitlab']['url']
        glServerToken = self.config.credentials['gitlab']['token']
        glServer = Gitlab(glServerConn, glServerToken)
        user = glServer.getUser(data['uuid'])
        if user:
            deleteResources['Gitlab'] = user

        if "ids" in deleteResources["Azure"]:
            provider.deleteResourceById(deleteResources["Azure"]["ids"])
        if "vhds" in deleteResources["Azure"]:
            provider.deleteStorageAccountContainer(data['uuid'])
        if "dns" in deleteResources["Azure"]:
            provider.deleteDNSRecord(deleteResources["Azure"]["dns"])
        if "Gitlab" in deleteResources:
            glServer.deleteUser(user)

        rsp = Response({
            "Resources": deleteResources
        })
        return rsp.httpResponse(200)

    def rebuildEnvironmentServer(self, data):
        """Rebuild a portion of an environment."""
        if not self.checkUUIDInUse(data['uuid']):
            rsp = Response({'error': 'Invalid UUID'})
            return rsp.httpResponse(404)
        response = list()
        template = self.templates.loadTemplate(
            data['infrastructureTemplateID']
        )
        provider = Azure(
            self.config.credentials['azure'],
            self.config.defaults['resource_group_name'],
            self.config.defaults['storage_account_name'],
            template,
            data['uuid']
        )
        print("Rebuilding: {}".format(data['servers']))
        resources = provider.getResources(id=data['uuid'], filter={
            'key': 'type',
            'value': data['servers']
        })

        vmDetails = list()
        if 'ids' in resources:
            for vm in resources['ids']:
                vmDetails.append(self.getVMDetails(vm, data['servers']))

            # Delete Resources
            provider.deleteResourceById(resources['ids'])
        else:
            vmDetails.append({'type': data['servers']})

        persistData = False
        if 'vhds' in resources:
            if data["persist_data"]:
                persistData = data['persist_data']
                # Delete OS Disks
                delDisks = list()
                for disk in resources['vhds']:
                    if 'data' not in disk:
                        delDisks.append(disk)
                if delDisks:
                    provider.deleteStorageAccountDisk(data['uuid'], delDisks)
            else:
                print("persist_data False")
                # Delete All Disks
                provider.deleteStorageAccountDisk(
                    data['uuid'],
                    resources['vhds']
                )

        count = None
        if 'ids' in resources:
            count = len(resources['ids'])

        # For some reason even if I created a template.copy()
        # the copy (templateCopy) was still being modivied by the provider
        # init. The copy() shoud break the reference...
        templateCopy = self.templates.loadTemplate(
            data['infrastructureTemplateID']
        )
        self.addVM(
            vmDetails,
            provider,
            templateCopy,
            data['uuid'],
            data['application'],
            count=count,
            persistData=persistData
        )
        for vmRsp in self.vms:
            response.append(vmRsp)
        rsp = Response({'Resources': response})
        return rsp.httpResponse(200)

    def scaleEnvironmentServer(self, data):
        """Scale an Environments servers."""
        if not self.checkUUIDInUse(data['uuid']):
            rsp = Response({'error': 'Invalid UUID'})
            return rsp.httpResponse(404)

        response = list()
        template = self.templates.loadTemplate(
            data['infrastructureTemplateID']
        )
        provider = Azure(
            self.config.credentials['azure'],
            self.config.defaults['resource_group_name'],
            self.config.defaults['storage_account_name'],
            template,
            data['uuid']
        )
        # For some reason even if I created a template.copy()
        # the copy (templateCopy) was still being modivied by the provider
        # init. The copy() shoud break the reference...
        templateCopy = self.templates.loadTemplate(
            data['infrastructureTemplateID']
        )
        resources = provider.getResources(id=data['uuid'], filter={
            'key': 'type',
            'value': data['servers']
        })
        currentSize = 0
        vms = list()
        if 'ids' in resources:
            currentSize = len(resources['ids'])
            for vm in resources['ids']:
                vms.append(self.getVMDetails(vm, data['servers']))
        else:
            vms.append({'type': data['servers']})
        response.append(vms)
        print("Scalling: {} from {} to {}".format(
            data['servers'],
            currentSize,
            data['count']
        ))

        if currentSize < data['count']:
            # Scale up
            self.addVM(
                vms,
                provider,
                templateCopy,
                data['uuid'],
                data['application'],
                count=data['count']
            )
        elif currentSize > data['count']:
            # Scale down
            deleteIds = list()
            deleteDisks = list()
            while len(vms) > data['count']:
                deleteIds.append(vms[-1]['id'])
                for disk in resources['vhds']:
                    if vms[-1]['name'] in disk:
                        deleteDisks.append(disk)
                vms.remove(vms[-1])
            provider.deleteResourceById(deleteIds)
            provider.deleteStorageAccountDisk(
                data['uuid'],
                deleteDisks
            )

        for vmRsp in self.vms:
            response.append(vmRsp)
        rsp = Response({'Resources': response})
        return rsp.httpResponse(200)
