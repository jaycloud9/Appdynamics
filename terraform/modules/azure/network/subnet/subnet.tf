variable "name"           { }
variable "environment"    { }
variable "owner"          { }
variable "purpose"        { }
variable "rg_name"        { }
variable "vnet_name"      { }
variable "stack"          { }
variable "subnet"         { }


resource "azurerm_subnet" "subnet" {
  name                  = "${var.environment}-${var.name}-${var.stack}-${var.purpose}-subnet"
  resource_group_name   = "${var.rg_name}"
  virtual_network_name  = "${var.vnet_name}"
  address_prefix        = "${var.subnet}"
}

output "${var.purpose}_subnet_id" { value = "${azurerm_subnet.subnet.id}" }
