variable "client_secret"  { }
variable "sub_id"					{ }
variable "tenant_id"			{ }
variable "client_id" 			{ }

variable "name"	          { }
variable "environment"    { }
variable "stack"          { }
variable "owner"          { }
variable "region"         { }

variable "subnet"         { }
variable "cidr"           { }
variable "dns_servers"    { }

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
  region        = "${var.region}"

}

module "storage" {
  source = "../../../modules/azure/storage"

  name          = "${var.name}"
  environment   = "${var.environment}"
  stack         = "${var.stack}"
  owner         = "${var.owner}"
  region        = "${var.region}"
  rg_name       = "${module.resource_group.name}"

  sa_type       = "Standard_LRS"
  purpose       = "vhd"

}

module "network" {
  source = "../../../modules/azure/network"

  name          = "${var.name}"
  environment   = "${var.environment}"
  stack         = "${var.stack}"
  owner         = "${var.owner}"
  region        = "${var.region}"
  cidr          = "${var.cidr}" 
  dns_servers   = "${var.dns_servers}"
  subnet        = "${var.subnet}"
  rg_name       = "${module.resource_group.name}"

}
