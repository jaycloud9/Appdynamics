variable "name"           { }
variable "environment"    { }
variable "owner"          { }
variable "stack"          { }
variable "region"         { }
variable "cidr"           { }
variable "dns_servers"    { }
variable "subnet"         { }

variable "rg_name"        { }

module "virtual_network" {
  source = "./virtual_network"

  name        = "${var.name}"
  environment = "${var.environment}"
  stack       = "${var.stack}"
  cidr        = "${var.cidr}"
  region      = "${var.region}"
  rg_name     = "${var.rg_name}"
  dns_servers = "${var.dns_servers}"
  owner       = "${var.owner}"
}

module "subnet" {
  source = "./subnet"

  name        = "${var.name}"
  environment = "${var.environment}"
  stack       = "${var.stack}"
  purpose     = "servers"
  rg_name     = "${var.rg_name}"
  subnet      = "${var.subnet}"
  vnet_name   = "${module.virtual_network.name}"
}

module "network_interface" {
  source      = "./network_interface"

  name        = "${var.name}"
  environment = "${var.environment}"
  stack       = "${var.stack}"
  region      = "${var.region}"
  rg_name     = "${var.rg_name}"
  owner       = "${var.owner}"
  subnet_id   = "${module.subnet.id}"
}
