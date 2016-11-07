provider "azurerm" {
  subscription_id = "404945c5-4730-450b-b243-8a15237fb808"
  client_id       = "c3ac0d69-381a-448a-a1e0-317bdfabc729"
  client_secret   = "***************************************"
  tenant_id       = "d5d2540f-f60a-45ad-86a9-e2e792ee6669"
}


# Create OSE-TF7_RG1 Resource Group
resource "azurerm_resource_group" "OSE-TF7_RG1" {
  name     = "OSE-TF7_RG1"
  location = "ukwest"
    tags {
    environment = "Test-OSE-TF7"
	Stack		= "ose"
	Team		= "utp-marketplace"
	Date		= "20161104"
	Use			= "tmptest"
	Resource	= "Resource-Group"
  }
}

# Create a virtual network in the OSE-TF7_RG1 Resource Group
resource "azurerm_virtual_network" "oseTF7rg1vnet1" {
  name                = "oseTF7rg1vnet1"
  address_space       = ["10.23.204.0/23"]
  location            = "ukwest"
  resource_group_name = "${azurerm_resource_group.OSE-TF7_RG1.name}"
  dns_servers         = ["10.44.5.101", "10.44.5.103"]
   tags {
    environment = "Test-OSE-TF7"
	Stack		= "ose"
	Team		= "utp-marketplace"
	Date		= "20161104"
	Use			= "tmptest"
	Resource	= "OSE-TF7-Virtual-network"
  }
}

# Create Gateway Subnet
resource "azurerm_subnet" "GatewaySubnet" {
  name                 = "GatewaySubnet"
  resource_group_name  = "${azurerm_resource_group.OSE-TF7_RG1.name}"
  virtual_network_name = "${azurerm_virtual_network.oseTF7rg1vnet1.name}"
  address_prefix 	   = "10.23.204.0/28"
}

# Create Servers Subnet
resource "azurerm_subnet" "Servers" {
  name                 = "Servers"
  resource_group_name  = "${azurerm_resource_group.OSE-TF7_RG1.name}"
  virtual_network_name = "${azurerm_virtual_network.oseTF7rg1vnet1.name}"
  address_prefix       = "10.23.205.0/24"
}

# Create NIC
resource "azurerm_network_interface" "OSETF7RG1VM1NIC1" {
    name = "OSETF7RG1VM1NIC1"
    location = "ukwest"
    resource_group_name  = "${azurerm_resource_group.OSE-TF7_RG1.name}"

    ip_configuration {
        name = "ipcon1OSETF7RG1VM1NIC1"
        subnet_id = "${azurerm_subnet.Servers.id}"
        private_ip_address_allocation = "dynamic"
    }
}

# Create TF-SA1-RG1 Resource Group
resource "azurerm_resource_group" "TF-SA1-RG1" {
  name     = "TF-SA1-RG1"
  location = "ukwest"
    tags {
    environment = "TF-SA1-RG1"
	Stack		= "ose"
	Team		= "utp-marketplace"
	Date		= "20161104"
	Use			= "tmptest"
	Resource	= "Resource-Group"
  }
}


resource "azurerm_storage_account" "tfsa1storacc1" {
    name = "tfsa1storacc1"
    resource_group_name = "${azurerm_resource_group.TF-SA1-RG1.name}"
    location = "ukwest"
    account_type = "Standard_LRS"

    tags {
     environment = "TF-SA1-RG1"
	 Stack		 = "ose"
	 Team		 = "utp-marketplace"
	 Date		 = "20161104"
	 Use		 = "tmptest"
	 Resource	 = "Storage-Account"
         }
}

resource "azurerm_storage_container" "tfsa1sc1vhds" {
    name = "tfsa1sc1vhds"
    resource_group_name = "${azurerm_resource_group.TF-SA1-RG1.name}"
    storage_account_name = "${azurerm_storage_account.tfsa1storacc1.name}"
    container_access_type = "private"
}


# Create Availability Set
resource "azurerm_availability_set" "osetf7rg1aset1" {
    name = "osetf7rg1aset1"
    location = "ukwest"
    resource_group_name   = "${azurerm_resource_group.OSE-TF7_RG1.name}"
    tags {
     environment = "OSE-TF7_RG1"
	 Stack		 = "ose"
	 Team		 = "utp-marketplace"
	 Date		 = "20161104"
	 Use		 = "tmptest"
	 Resource	 = "availability-set"
         }
}

resource "azurerm_virtual_machine" "OSETF7RG1VM1" {
    name = "OSETF7RG1VM1"
    location = "ukwest"
    resource_group_name   = "${azurerm_resource_group.OSE-TF7_RG1.name}"
    network_interface_ids = ["${azurerm_network_interface.OSETF7RG1VM1NIC1.id}"]
    vm_size               = "Standard_A0"
     availability_set_id  = "${azurerm_availability_set.osetf7rg1aset1.id}"

    storage_image_reference {
        publisher = "RedHat"
        offer = "RHEL"
        sku = "7.2"
        version = "latest"
    }

    storage_os_disk {
        name = "OSETF7RG1VM1OSDSK"
        vhd_uri = "${azurerm_storage_account.tfsa1storacc1.primary_blob_endpoint}${azurerm_storage_container.tfsa1sc1vhds.name}/testvm1osdisk1.vhd"
        caching = "ReadWrite"
        create_option = "FromImage"
    }

    os_profile {
        computer_name = "OSETF7RG1VM1"
        admin_username = "TFAdmin"
        admin_password = "4TFadm1n99"
    }

   tags {
    environment = "Test-OSE-TF7"
	Stack		= "ose"
	Team		= "utp-marketplace"
	Date		= "20161104"
	Use			= "tmptest"
	Resource	= "OSE-TF7-OSETF7RG1VM1"
       }
}
