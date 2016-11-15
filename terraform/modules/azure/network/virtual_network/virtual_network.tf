variable "name"						{ }
variable "environment"		{ }
variable "owner"					{ }
variable "cidr"						{ }
variable "dns_servers"		{ }
variable "rg_name"				{ }
variable "stack"          { }
variable "region"         { }


resource "azurerm_virtual_network" "stack_network" {
  name                = "${var.environment}-${var.name}-${var.stack}-vnet"
  address_space       = ["${var.cidr}"]
  location            = "${var.region}"
  resource_group_name = "${var.rg_name}"
  dns_servers         = ["${split(",", var.dns_servers)}"]
  tags {
    Environment = "${var.environment}"
    Stack       = "${var.stack}"
    Owner       = "${var.owner}"
  }
}


output "id"     { value = "${azurerm_virtual_network.stack_network.id}" }
output "name"   { value = "${azurerm_virtual_network.stack_network.name}" }
