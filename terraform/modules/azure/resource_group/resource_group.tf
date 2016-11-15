variable "name"					{ }
variable "environment"	{ }
variable "region"				{ default = "ukwest"}
variable "stack"				{ }
variable "owner"				{ }

resource "azurerm_resource_group" "env_rg" {
  name     = "${var.environment}-${var.name}-${var.stack}-rg"
  location = "${var.region}"
  tags {
    Environment = "${var.environment}"
  	Stack   		= "${var.stack}"
  	Owner    		= "${var.owner}"
  }
}

output "id"     { value = "${azurerm_resource_group.env_rg.id}" }
output "name"   { value = "${azurerm_resource_group.env_rg.name}" }
