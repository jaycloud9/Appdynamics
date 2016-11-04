provider "azurerm" {
  subscription_id = "404945c5-4730-450b-b243-8a15237fb808"
  client_id       = "c3ac0d69-381a-448a-a1e0-317bdfabc729"
  client_secret   = "6edc4Yoon/iyxVS8IVxUfGY87o5iN1bEpVir8WIWgMM="
  tenant_id       = "d5d2540f-f60a-45ad-86a9-e2e792ee6669"
}

resource "azurerm_resource_group" "OSE-TF_RG1" {
  name     = "OSE-TF_RG1"
  location = "ukwest"
}


