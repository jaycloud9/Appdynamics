variable "name"           { }
variable "environment"    { }
variable "owner"          { }
variable "region"					{ }
variable "stack"					{ }

variable "rg_name"        { }
variable "sa_type"        { default = "Standard_LRS" }

resource "azurerm_storage_account" "storage_account" {
	name = "${var.environment}${var.name}${var.stack}sa"
	resource_group_name = "${var.rg_name}"
	location = "${var.region}"
	account_type = "${var.sa_type}"
  
	tags {
    Environment = "${var.environment}"
    Stack       = "${var.stack}"
    Owner       = "${var.owner}"
  }
}

output "id"       { value = "${azurerm_storage_account.storage_account.id}" }
output "name"     { value = "${azurerm_storage_account.storage_account.name}" }
output "endpoint" { value = "${azurerm_storage_account.storage_account.primary_blob_endpoint}" }
