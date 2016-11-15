variable "name"						{ }
variable "environment"		{ }
variable "stack"          { }
variable "owner"					{ }
variable "subnet_id"		  { }
variable "rg_name"				{ }
variable "region"         { }

resource "azurerm_network_interface" "NIC" {
  name  = "${var.environment}-${var.name}-${var.stack}-vnet"
  location  = "${var.region}"
  resource_group_name = "${var.rg_name}"

  ip_configuration {
    name = "${var.environment}-${var.name}-${var.stack}-ipconf"
    subnet_id = "${vr.subnet_id}"
    private_ip_address_allocation = "dynamic"
  }
  tags {
    Environment = "${var.environment}"
    Stack       = "${var.stack}"
    Owner       = "${var.owner}"
  }
}

output "id" { value = "${azurerm_network_interface.NIC.id}" }
