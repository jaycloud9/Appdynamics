variable "name"           { }
variable "environment"    { }
variable "region"					{ }
variable "stack"					{ }

variable "rg_name"        { }
variable "sa_name"        { }
variable "purpose"        { }

resource "azurerm_storage_container" "storage_container" {
	name = "${var.environment}-${var.name}-${var.stack}-sa-${var.purpose}"
	resource_group_name = "${var.rg_name}"
  storage_account_name = "${var.sa_name}"
  container_access_type = "private"
}

output "id" { value = "${azurerm_storage_container.storage_container.id}" }
output "name" { value = "${azurerm_storage_container.storage_container.name}" }
