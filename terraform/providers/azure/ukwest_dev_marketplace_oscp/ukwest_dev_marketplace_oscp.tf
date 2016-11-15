variable "client_secret"  { }
variable "sub_id"					{ }
variable "tenant_id"			{ }
variable "client_id" 			{ }

variable "name"	          { }
variable "environment"    { }
variable "stack"          { }
variable "owner"          { }

provider "azurerm" {
  subscription_id = "${var.sub_id}"
  client_id       = "${var.client_id}"
  client_secret   = "${var.client_secret}"
  tenant_id       = "${var.tenant_id}"
}

module "resource_group" {
  source = "../../../modules/azure/resource_group"

  name          = "${var.name}"
  environment   = "${var.environment}"
  stack         = "${var.stack}"
  owner         = "${var.owner}"

}

#module "network" {
#  source = "../../../modules/azure/network"
#
#
#}
