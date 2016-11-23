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

variable "tf_user"        { }
variable "tf_user_password" { }
variable "public_key"     { }


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

module "compute" {
  source = "../../../modules/azure/compute"

  name          = "${var.name}"
  environment   = "${var.environment}"
  stack         = "${var.stack}"
  owner         = "${var.owner}"
  region        = "${var.region}"
  rg_name       = "${module.resource_group.name}"

  gitlab_network_inf        = "${module.network.gitlab_network_interface_id}"
  master_network_inf        = "${module.network.master_network_interface_id}"
  node_infra_network_inf    = "${module.network.node_infra_network_interface_id}"
  node_worker_network_inf   = "${module.network.node_worker_network_interface_id}"
  formation_network_inf     = "${module.network.formation_network_interface_id}"
  storage_network_inf       = "${module.network.storage_network_interface_id}"

  os_storage_container = "${module.storage.sa_endpoint}${module.storage.sa_container_name}"
  tf_user       = "${var.tf_user}"
  tf_admin_password = "${var.tf_user_password}"
  public_key    = "${var.public_key}"
  vm_size       = "Standard_A0"

}
