provider "azurerm" {
  subscription_id = "404945c5-4730-450b-b243-8a15237fb808"
  client_id       = "c3ac0d69-381a-448a-a1e0-317bdfabc729"
  client_secret   = "6edc4Yoon/iyxVS8IVxUfGY87o5iN1bEpVir8WIWgMM="
  tenant_id       = "d5d2540f-f60a-45ad-86a9-e2e792ee6669"
}

resource "azurerm_resource_group" "OSE-TF4_RG1" {
  name     = "OSE-TF3_RG1"
  location = "ukwest"
}


resource "azurerm_virtual_network" "OSE-TF4_RG1" {
  name                = "osetf4rg1vnet1"
  resource_group_name = "${azurerm_resource_group.OSE-TF4_RG1.name}"
  address_space       = ["10.23.202.0/23"]
  location            = "ukwest"
  dns_servers         = ["10.44.5.101", "10.44.5.103"]

  subnet {
    name           = "GatewaySubnet"
    address_prefix = "10.23.202.0/28"
  }

  tags {
    environment = "Test-OSE-TF4"
	Stack		= "ose"
	Team		= "utp-marketplace"
	Date		= "20161104"
	Use			= "tmptest"
	Resource	= "vnet-subnets"
  }
}

resource "azurerm_subnet" "OSE-TF4_RG1" {
    name = "Servers"
    resource_group_name = "${azurerm_resource_group.OSE-TF4_RG1.name}"
    virtual_network_name = "${azurerm_virtual_network.OSE-TF4_RG1.name}"
    address_prefix = "10.23.203.0/24"
}

resource "azurerm_network_interface" "OSE-TF4_RG1" {
    name = "OSETF4RG1VM1NIC1"
    location            = "ukwest"
    resource_group_name = "${azurerm_resource_group.OSE-TF4_RG1.name}"

    ip_configuration {
        name = "ipcon1OSETF4RG1VM1NIC1"
        subnet_id = "${azurerm_subnet.OSE-TF4_RG1.id}"
        private_ip_address_allocation = "dynamic"
    }

    tags {
     environment = "Test-OSE-TF4"
 	 Stack		= "ose"
	 Team		= "utp-marketplace"
	 Date		= "20161104"
	 Use		= "tmptest"
	 Resource	= "vnet-subnets-nics"
    }
}

