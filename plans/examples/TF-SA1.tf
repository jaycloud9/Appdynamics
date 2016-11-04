provider "azurerm" {
  subscription_id = "404945c5-4730-450b-b243-8a15237fb808"
  client_id       = "c3ac0d69-381a-448a-a1e0-317bdfabc729"
  client_secret   = "6edc4Yoon/iyxVS8IVxUfGY87o5iN1bEpVir8WIWgMM="
  tenant_id       = "d5d2540f-f60a-45ad-86a9-e2e792ee6669"
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
