"""PlatformInfra Controller.

The controller orchestrates the main actions of the platform.
This includes calling the underlying provider methods and the simpler
additional actions such as Jenkins and gitlab.

"""

from platforminfra.templates import Template
from platforminfra.config import Config
from platforminfra.infrastructure.azure import Azure
from multiprocessing import Process, Queue, Lock
from copy import deepcopy

from ..helpers import Jenkins, Gitlab, Helpers
import re


class Controller(object):
    """Controls the platformInfra.

    The controller Object carries out all of the actions.
    As this expands it will be neccessary to move the control of the
    infrastructure into its own module. For now the boundaries between Control
    and provider are blurred. The provider works on the resource and sometimes
    *with* the resource whereas the controller only works *with* the resource.
    """

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
        """Create the tags property."""
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

    def getResourceDetails(self, id):
        """Get a VM object back from an ID."""
        resource = dict()
        resource['id'] = id
        idSplit = re.split(r"/", id.strip())
        resource['name'] = idSplit[-1]
        resource['type'] = idSplit[6] + "/" + idSplit[7]
        resource['group'] = idSplit[4]

        return resource

    def getVmList(self, provider, uuid, server):
        """Return a list of VM's and their current running state."""
        resources = provider.getResources(id=uuid, filter={
            'key': 'type',
            'value': server
        })
        if 'ids' in resources:
            statuses = self.getStatusById(resources['ids'], provider)
            return statuses
        else:
            raise Exception({
                'error': "No VM Resources found for {} in {}".format(
                    server,
                    uuid
                ),
                'code': 404
            })

    def getVMDetails(self, id, server):
        """Get a VM object back from an ID."""
        vm = dict()
        vm['id'] = id
        idSplit = re.split(r"/", id.strip())
        vm['name'] = idSplit[-1]
        vm['type'] = idSplit[6] + "/" + idSplit[7]
        vm['server'] = server
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
                            lbResName = 'Microsoft.Network/loadBalancers'
                            if resourceType == lbResName and \
                                    lbName in resourceName:
                                print("Getting LB")
                                # Found the Id of the Load balancer
                                # for the server
                                lb = provider.getResourceById(resourceType, id)
                                be = lb.properties['backendAddressPools'][0]
                                beId = be['id']
        return beId

    def runJenkinsPipeline(self, pipeline):
        """Run a specified Jenkins pipeline."""
        jenkinsServer = Jenkins(
            self.config.credentials['jenkins']['url'],
            user=self.config.credentials['jenkins']['user'],
            password=self.config.credentials['jenkins']['password']
        )
        print("Running Jenkins Job")
        jenkinsServer.runBuildWithParams(
            pipeline,
            params={
                "UUID": self.tags['uuid']
            }
        )

    def getJenkinsBuildStatus(self, pipeline, uuid):
        """Get a pipeline status for a given uuid."""
        jenkinsServer = Jenkins(
            self.config.credentials['jenkins']['url'],
            user=self.config.credentials['jenkins']['user'],
            password=self.config.credentials['jenkins']['password']
        )
        status = jenkinsServer.getBuildStatus(
            pipeline,
            uuid
        )
        return status

    def checkJenkinsRunning(self, pipeline, uuid):
        """Check a list of responses and return boolean."""
        statuses = self.getJenkinsBuildStatus(pipeline, uuid)
        running = False
        for status in statuses:
            if status['status'] == 'RUNNING':
                running = True
        return running

    def runGitlabTasks(self, gitlab):
        """Run the required actrions for Gitlab creation."""
        response = dict()
        print("Connecting to Gitlab")
        glServerConn = self.config.credentials['gitlab']['url']
        glServerToken = self.config.credentials['gitlab']['token']
        glSourceTeam = "root"
        glServer = Gitlab(glServerConn, glServerToken)

        print("Create user")
        password = Helpers.randStr(10)
        if 'password' in gitlab['user']:
            password = gitlab['user']['password']
        user = glServer.createUser(
            self.tags['uuid'],
            self.tags['uuid'],
            password,
            self.tags['uuid'] + '@example.net'
        )

        if 'sshKey' in gitlab['user']:
            key = glServer.addSshKey(user, gitlab['user']['sshKey'])
            if type(key) is dict:
                if 'error' in key:
                    raise Exception(key)
        response['user'] = user.username
        if 'cloneRepos' in gitlab:
            response['repos'] = dict()
            for repo in gitlab['cloneRepos']:
                glSourceProject = glServer.getProject(glSourceTeam, repo)
                if type(glSourceProject) is dict:
                    if 'error' in glSourceProject:
                        raise Exception(glSourceProject)
                forked = glServer.forkProject(
                    user.username,
                    glSourceProject.id
                )
                if type(forked) is dict:
                    if 'error' in forked:
                        raise Exception(forked)
                response['repos'][repo] = forked.web_url

        return response

    def addVM(
            self, vms, provider, template, uuid, application=None,
            count=None, persistData=False
            ):
        """Given an Existing list of VMs Add more."""
        if not count:
            for server in template['services']['servers']:
                if server['name'] == vms[0]['server']:
                    count = server['count']
        vm = dict()
        vm['count'] = count
        print("Getting BE ID")
        beId = self.getVMBEID(
            provider,
            template=template,
            server=vms[0]['server'],
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
        vm['name'] = vms[0]['server']
        vmList = [vm]
        # There's only a single subnet per network
        netName = template['services']['networks'][0]['name']
        subnet = provider.getSubnetID(uuid + netName + "0")
        self.tags['uuid'] = uuid
        self.subnets.append({'subnets': {uuid: subnet}})
        self.createVms(vmList, provider, persistData)

        if 'application':
            self.runJenkinsPipeline(application)

    def getStatusById(self, ids, provider):
        """Get the status of a resource."""
        statuses = list()
        for id in ids:
            details = self.getResourceDetails(id)
            item = provider.getResourceById(details['type'], details['id'])
            if 'provisioningState' in item.properties:
                tmpItem = {
                    'name': details['name'],
                    'type': details['type'],
                    'resourceGroup': details['group'],
                    'provisioningState': item.properties['provisioningState']
                }
                if item.type == "Microsoft.Compute/virtualMachines":
                    vmData = provider.getVmInfo(
                        item.name,
                        item.id,
                        details['group']
                    )
                    for status in vmData.instance_view.statuses:
                        if 'PowerState' in status.code:
                            tmpItem['status'] = status.display_status
                    disks = list()
                    for disk in vmData.instance_view.disks:
                        for status in disk.statuses:
                            disks.append({
                                "name": disk.name,
                                "provisioningState": status.display_status
                            })
                    tmpItem['disks'] = disks
            else:
                if details['type'] == 'Microsoft.Compute/availabilitySets':
                    tmpItem = {
                        'name': details['name'],
                        'type': details['type'],
                        'resourceGroup': details['group'],
                        'provisioningState': 'Succeeded'
                    }
                else:
                    tmpItem = {
                        'name': details['name'],
                        'type': details['type'],
                        'resourceGroup': details['group'],
                        'provisioningState': 'Unknown'
                    }
            statuses.append(tmpItem)
        return statuses

    def checkVMResources(self, vmName, resources):
        """Given a VM Name does it have the right resources."""
        vm = dict()
        vm['vm'] = False
        vm['nic'] = False
        vm['pip'] = False
        vm['disks'] = False
        vm['name'] = vmName
        for resource in resources:
            if resource['type'] == "Microsoft.Compute/virtualMachines"\
                    and vmName in resource['name']:
                    if resource['provisioningState'] == 'Succeeded':
                        vm['vm'] = True
                    disks = list()
                    for disk in resource['disks']:
                        if 'succeeded' in disk['provisioningState']:
                            disks.append(True)
                        else:
                            disks.append(False)
                    if all(disks):
                        vm['disks'] = True

            if resource['type'] == "Microsoft.Network/networkInterfaces"\
                    and vmName in resource['name']:
                    vm['nic'] = True
            if resource['type'] == "Microsoft.Network/publicIPAddresses"\
                    and vmName in resource['name']:
                    vm['pip'] = True
        return vm

    def compareResources(self, statusRes, deploymentRes, uuid):
        """Compare a status list with the Deployment resources.

        Loop through the expected resources (deploymnetRes) and ensure at least
        one of each is found in the statusRes so we inform the request if all
        resources are 'okay' or not.
        """
        deployNetworkCount = list()
        for resource in deploymentRes['resources']:
            if 'networks' in resource:
                for network in resource['networks']:
                    deployNetworkCount.append(network['name'])
        statusNetworkCount = list()
        statusVmCount = list()
        for i in statusRes:
            if "Environment resources" in i:
                for resource in i["Environment resources"]:
                    if resource['type'] == "Microsoft.Network/virtualNetworks":
                        statusNetworkCount.append(resource['name'])
                    if resource['type'] == "Microsoft.Compute/virtualMachines":
                        statusVmCount.append(self.checkVMResources(
                                resource['name'],
                                i["Environment resources"]
                            )
                        )
        # Create a list of all of the broken resources so they can be eaisly
        # displayed within the status response.
        brokenResources = list()
        for vm in statusVmCount:
            # If a VM Does not have these it is not 'good'
            if not (vm['vm'] and vm['nic'] and vm['pip'] and vm['disks']):
                print("VM {} is broken".format(vm['name']))
                brokenResources.append({
                    'name': vm['name'],
                    'type': "Microsoft.Compute/virtualMachines",
                    'status': "Failed"
                })

        for network in deployNetworkCount:
            for statusNetwork in statusNetworkCount:
                if network not in statusNetwork:
                    brokenResources.append({
                        'name': network,
                        'type': "Microsoft.Network/virtualNetworks",
                        'status': "Failed"
                    })

        return brokenResources

    def createNetworks(self, data, provider):
        """Create Networks."""
        # Must complete before everything else is built
        subNets = Queue()
        print("Creating network")
        netProcs = list()
        try:
            for idx, network in enumerate(data):
                netId = str(self.tags['uuid'])+network['name']+str(idx)
                p = Process(
                    target=provider.network,
                    args=(network, netId, self.tags, subNets)
                )
                netProcs.append(p)
                p.start()

            subnets = dict()
            for proc in netProcs:
                lives = 600
                while True:
                    # Wait for 1 seconds then take a life
                    proc.join(1)
                    lives = lives - 1
                    if not subNets.empty():
                        subnets['subnets'] = subNets.get()
                        # break the while true
                        break
                    elif lives <= 0:
                        if proc.is_alive():
                            # If it's been 600 seconds and we're trapped in the
                            # while loop. Kill the process.
                            proc.terminate()
                            raise Exception({
                                'error': "Took too long",
                                'code': 500
                            })
                        else:
                            print("Proc Dead already")
                            # Process already dead
                            break
        except Exception as e:
            if e.args[0] is dict:
                raise
            else:
                raise Exception({
                    'error': "Unknown error while creating networks: {}"
                    .format(str(e))
                })

        self.subnets.append(subnets)

    def stopVM(self, provider, vm):
        """Stop a running VM."""
        provider.stopVm(vm['name'], vm['resourceGroup'])

    def startVM(self, provider, vm):
        """Start a stopped VM."""
        provider.startVm(vm['name'], vm['resourceGroup'])

    def createVms(self, data, provider, persistData=False):
        """Create VMs.

        For a given set of data, for each 'server' group create each server
        with all of dependencies each VM needs.
        """
        print("Creating Servers")
        vms = Queue()
        vmLock = Lock()
        # Processes that can be run in parrallel
        serverProcs = list()
        try:
            for i in self.subnets:
                if self.tags['uuid'] in i['subnets']:
                    # Grab A subnet - needs reworking when multiple networks is
                    # supported
                    vmSubnet = i['subnets'][self.tags['uuid']]
            for server in data:
                # For each 'server' Spawn a process to create that vm
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
                    'process': p
                }
                if 'dns' in server:
                    vmDetails['dns'] = server['dns']
                serverProcs.append(vmDetails)
                p.start()

            for proc in serverProcs:
                lives = 600
                while True:
                    # Wait for 1 seconds then take a life
                    proc['process'].join(1)
                    lives = lives - 1
                    if not vms.empty():
                        tmpData = vms.get()
                        # break the while true
                        break
                    elif lives <= 0:
                        if proc['process'].is_alive():
                            # If it's been 600 seconds and we're trapped in the
                            # while loop. Kill the process.
                            proc.terminate()
                            raise Exception({
                                'error': "Took too long",
                                'code': 500
                            })
                        else:
                            # Process already dead
                            break
                if 'dns' in proc:
                    # Only apply to the first server
                    result = provider.addDNS(
                        tmpData['vms'][0]['public_ip'],
                        proc['dns'] + '-' + self.tags['uuid']
                    )
                    tmpData['dns'] = result
                self.vms.append(tmpData)
        except Exception as e:
            if e.args[0] is dict:
                raise
            else:
                raise Exception({
                    'error': "Unknown error while creating Vms: {}"
                    .format(str(e))
                })

    def createLoadBalancer(self, lbName, lbDetails, provider, lbQueue):
        """Create One loadbalancer and it's dependent Servers."""
        # Create LB here
        print("Creating LB: {}".format(lbName))
        lbData = provider.loadBalancer(lbDetails['load_balancer'], self.tags)
        lbDetails['servers']['beId'] = lbData['lbInfo'] \
            .backend_address_pools[0].id
        # Create a single item list so we can re-use createVms
        serverList = list()
        serverList.append(lbDetails['servers'])
        self.createVms(serverList, provider)
        record = self.tags['uuid']
        if 'domain' in lbDetails['load_balancer']:
            record = lbDetails['load_balancer']['domain'] + '-' + record
        else:
            record = lbDetails['load_balancer']['name'] + '-' + record

        result = provider.addDNS(
            lbData['publicIp'].ip_address,
            record
        )
        lbQueue.put({
            lbDetails['load_balancer']['name']: result
        })

    def validateLoadBalancer(self, lb):
        """Validate a LB's config."""
        validate = False
        if lb['health_protocol'] == 'Tcp' or \
                lb['health_protocol'] == 'Http':
            if lb['health_protocol'] == 'Http':
                if 'health_path' not in lb:
                    e = {
                        'error': "Must specify health_path with Http"
                    }
                    raise Exception(e)
            validate = True
        else:
            e = {
                'error': "health_protocol must be 'Http' or 'Tcp'"
            }
            raise Exception(e)

        print("LB Validated as {}".format(validate))
        return validate

    def createLoadBalancers(self, data, provider):
        """Create Load balancers."""
        print("Creating Load Balancers")
        lbQueue = Queue()
        lbProcList = list()
        try:
            for item in data:
                for lbName, details in item.items():
                    # For each LB Spawn a child process
                    if self.validateLoadBalancer(details['load_balancer']):
                        p = Process(
                            target=self.createLoadBalancer,
                            args=(lbName, details, provider, lbQueue)
                        )
                        lbProcList.append(p)
                        p.start()
            for proc in lbProcList:
                lives = 600
                while True:
                    # Wait for 1 seconds then take a life
                    proc['process'].join(1)
                    lives = lives - 1
                    if not lbQueue.empty():
                        tmpData = lbQueue.get()
                        # break the while true
                        break
                    elif lives <= 0:
                        if proc['process'].is_alive():
                            # If it's been 600 seconds and we're trapped in the
                            # while loop. Kill the process.
                            proc.terminate()
                            raise Exception({
                                'error': "Took too long",
                                'code': 500
                            })
                        else:
                            # Process already dead, but no data came back
                            raise Exception({
                                'error': "Unknown error while creating LB: {}"
                                .format(lbName)
                            })

                self.lbs.append(tmpData)
        except Exception as e:
            if e.args[0] is dict:
                raise
            else:
                raise Exception({
                    'error': "Unknown error while creating LBs: {}"
                    .format(str(e))
                })

    def createEnvironment(self, data):
        """Create an Environment.

        From a Infrastructure template create an environment.
        """
        if 'infrastructureTemplateID' in data:
            template = self.templates.loadTemplate(
                data['infrastructureTemplateID']
            )
        else:
            raise Exception({
                'error': 'infrastructureTemplateID must be provided',
                'code': 400
            })
        if 'id' in data:
            if self.checkUUIDInUse(data['id']):
                raise Exception({'error': 'UUID in use', 'code': 412})
        else:
            raise Exception({'error': 'ID must be provided', 'code': 400})
        if 'application' in data:
            # This should never happen as the check for UUID should throw first
            if self.checkJenkinsRunning(data['application'], data['id']):
                raise Exception({
                    'error': 'Jenkins build running already',
                    'code': 409
                })

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
            raise Exception({
                'error': provider.credentials['error'],
                'code': 400}
            )

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
        except:
            raise

        for vmRsp in self.vms:
            response.append(vmRsp)

        # By this point an environment should be created so Execute Jenkins job
        if 'application' in data:
            self.runJenkinsPipeline(data['application'])

        if 'gitlab' in data:
            glResponse = self.runGitlabTasks(data['gitlab'])
            response.append({'gitlab': glResponse})
        if self.lbs:
            response = response + self.lbs
        return {'msg': {'Resources': response}, 'code': 201}

    def listEnvironments(self):
        """Return a list of environments."""
        provider = Azure(
            self.config.credentials['azure'],
            self.config.defaults['resource_group_name'],
            self.config.defaults['storage_account_name']
        )

        return {'msg': {"Environments": provider.getResources()}, 'code': 200}

    def deleteEnvironment(self, data):
        """Delete a specific Environments Resources."""
        if not self.checkUUIDInUse(data['uuid']):
            raise Exception({'error': 'Invalid UUID', 'code': 404})
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

        return {'code': 204, 'msg': None}

    def rebuildEnvironmentServer(self, data):
        """Rebuild a portion of an environment.

        Given a specified 'server' group delete and recreate those servers.
        """
        if 'infrastructureTemplateID' in data:
            template = self.templates.loadTemplate(
                data['infrastructureTemplateID']
            )
            templateCopy = deepcopy(template)
        else:
            raise Exception({
                'error': 'infrastructureTemplateID must be provided',
                'code': 400
            })
        if 'uuid' in data:
            if not self.checkUUIDInUse(data['uuid']):
                raise Exception({'error': 'Invalid UUID', 'code': 404})
        else:
            raise Exception({'error': 'ID must be provided', 'code': 400})
        if 'application' in data:
            if self.checkJenkinsRunning(data['application'], data['uuid']):
                raise Exception({
                    'error': 'Jenkins build running already',
                    'code': 409
                })

        response = list()
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
            if data["persistData"]:
                persistData = data['persistData']
                # Delete OS Disks
                delDisks = list()
                for disk in resources['vhds']:
                    if 'data' not in disk:
                        delDisks.append(disk)
                if delDisks:
                    provider.deleteStorageAccountDisk(data['uuid'], delDisks)
            else:
                print("persistData False")
                # Delete All Disks
                provider.deleteStorageAccountDisk(
                    data['uuid'],
                    resources['vhds']
                )

        count = None
        if 'ids' in resources:
            count = len(resources['ids'])

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
        return {'msg': {'Resources': response}, 'code': 200}

    def scaleEnvironmentServer(self, data):
        """Scale an Environments servers."""
        if 'infrastructureTemplateID' in data:
            template = self.templates.loadTemplate(
                data['infrastructureTemplateID']
            )
            templateCopy = deepcopy(template)
        else:
            raise Exception({
                'error': 'infrastructureTemplateID must be provided',
                'code': 400
            })
        if 'uuid' in data:
            if not self.checkUUIDInUse(data['uuid']):
                raise Exception({'error': 'Invalid UUID', 'code': 404})
        else:
            raise Exception({'error': 'ID must be provided', 'code': 400})
        if 'application' in data:
            if self.checkJenkinsRunning(data['application'], data['uuid']):
                raise Exception({
                    'error': 'Jenkins build running already',
                    'code': 409
                })

        response = list()
        provider = Azure(
            self.config.credentials['azure'],
            self.config.defaults['resource_group_name'],
            self.config.defaults['storage_account_name'],
            template,
            data['uuid']
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
            vms.append({'server': data['servers']})
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
        return {'msg': {'Resources': response}, 'code': 200}

    def environmentStatus(self, data):
        """Get the status of an environment."""
        if 'infrastructureTemplateID' in data:
            template = self.templates.loadTemplate(
                data['infrastructureTemplateID']
            )
        else:
            raise Exception({
                'error': 'infrastructureTemplateID must be provided',
                'code': 400
            })
        if 'uuid' in data:
            if not self.checkUUIDInUse(data['uuid']):
                raise Exception({'error': 'Invalid UUID', 'code': 404})
        else:
            raise Exception({'error': 'ID must be provided', 'code': 400})

        statusResoures = list()
        provider = Azure(
            self.config.credentials['azure'],
            self.config.defaults['resource_group_name'],
            self.config.defaults['storage_account_name'],
            template,
            data['uuid']
        )
        print("Getting Status")
        deploymentResources = provider.resources
        resources = provider.getResources(id=data['uuid'])
        if 'ids' in resources:
            statusResoures.append({
                'Environment resources':
                self.getStatusById(resources['ids'], provider)
            })
        if 'dns' in resources:
            dnsEntry = list()
            for entry in resources['dns']:
                dnsEntry.append({
                    'name': entry,
                    'type': 'Microsoft.Network/dnsZones',
                    'status': 'Succeeded'
                })
            statusResoures.append({'Shared resources': dnsEntry})
        if 'vhds' in resources:
            vhdEntry = list()
            for vhd in resources['vhds']:
                vhdEntry.append({
                    'name': vhd,
                    'type': 'Microsoft.Stroage/blobStorage',
                    'status': 'Succeeded'
                })
            statusResoures.append({
                'Storage resources': vhdEntry
            })
        if 'application' in data:
            jenkinsStatus = self.getJenkinsBuildStatus(
                data['application'],
                data['uuid']
            )
            statusResoures.append({
                'Build resources': jenkinsStatus
            })

        broken = self.compareResources(
            statusResoures,
            deploymentResources,
            data['uuid']
        )
        response = {
            'Resources': statusResoures,
            'status': "Succeeded"
        }
        if broken:
            statusResoures.append({
                'Broken resources': broken
            })
            response['status'] = "Failed"

        return {'msg': response, 'code': 200}

    def environmentServerStopStart(self, data, action):
        """Stop or Start an environment."""
        if not self.checkUUIDInUse(data['uuid']):
            raise Exception({'error': 'Invalid UUID', 'code': 404})
        if 'application' in data:
            if self.checkJenkinsRunning(data['application'], data['uuid']):
                raise Exception({
                    'error': 'Jenkins build running already',
                    'code': 409
                })
        provider = Azure(
            self.config.credentials['azure'],
            self.config.defaults['resource_group_name'],
            self.config.defaults['storage_account_name'],
            id=data['uuid']
        )
        VMList = self.getVmList(provider, data['uuid'], data['servers'])

        outcome = {
            'stop': 'VM running',
            'start': 'VM stopped'
        }
        actions = {
            'stop': self.stopVM,
            'start': self.startVM
        }

        for vm in VMList:
            if vm['status'] == outcome[action]:
                actions[action](provider, vm)
        statuses = self.getVmList(provider, data['uuid'], data['servers'])
        return {'msg': {'VMs': statuses}, 'code': 200}
