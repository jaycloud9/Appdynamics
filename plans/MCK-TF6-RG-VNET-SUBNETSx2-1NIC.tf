provider "azurerm" {
  subscription_id = "404945c5-4730-450b-b243-8a15237fb808"
  client_id       = "c3ac0d69-381a-448a-a1e0-317bdfabc729"
  client_secret   = "6edc4Yoon/iyxVS8IVxUfGY87o5iN1bEpVir8WIWgMM="
  tenant_id       = "d5d2540f-f60a-45ad-86a9-e2e792ee6669"
}

# Create OSE-TF6_RG1 Resource Group
resource "azurerm_resource_group" "OSE-TF6_RG1" {
  name     = "OSE-TF6_RG1"
  location = "ukwest"
    tags {
    environment = "Test-OSE-TF6"
	Stack		= "ose"
	Team		= "utp-marketplace"
	Date		= "20161104"
	Use			= "tmptest"
	Resource	= "Resource-Group"
  }
}

# Create a virtual network in the OSE-TF6_RG1 Resource Group
resource "azurerm_virtual_network" "oseTF6rg1vnet1" {
  name                = "oseTF6rg1vnet1"
  address_space       = ["10.23.202.0/23"]
  location            = "ukwest"
  resource_group_name = "${azurerm_resource_group.OSE-TF6_RG1.name}"
  dns_servers         = ["10.44.5.101", "10.44.5.103"]
   tags {
    environment = "Test-OSE-TF6"
	Stack		= "ose"
	Team		= "utp-marketplace"
	Date		= "20161104"
	Use			= "tmptest"
	Resource	= "OSE-TF6-Virtual-network"
  }
}

# Create Gateway Subnet
resource "azurerm_subnet" "GatewaySubnet" {
  name                 = "GatewaySubnet"
  resource_group_name  = "${azurerm_resource_group.OSE-TF6_RG1.name}"
  virtual_network_name = "${azurerm_virtual_network.oseTF6rg1vnet1.name}"
  address_prefix 	   = "10.23.202.0/28"
}

# Create Servers Subnet
resource "azurerm_subnet" "Servers" {
  name                 = "Servers"
  resource_group_name  = "${azurerm_resource_group.OSE-TF6_RG1.name}"
  virtual_network_name = "${azurerm_virtual_network.oseTF6rg1vnet1.name}"
  address_prefix       = "10.23.203.0/24"
}

# Create NIC
resource "azurerm_network_interface" "OSETF6RG1VM1NIC1" {
    name = "OSETF6RG1VM1NIC1"
    location = "ukwest"
    resource_group_name  = "${azurerm_resource_group.OSE-TF6_RG1.name}"

    ip_configuration {
        name = "ipcon1OSETF6RG1VM1NIC1"
        subnet_id = "${azurerm_subnet.Servers.id}"
        private_ip_address_allocation = "dynamic"
    }
}

