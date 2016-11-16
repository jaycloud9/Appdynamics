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

module "servers_subnet" {
  source = "./subnet"

  name        = "${var.name}"
  environment = "${var.environment}"
  stack       = "${var.stack}"
  purpose     = "servers"
  rg_name     = "${var.rg_name}"
  subnet      = "${var.subnet}"
  vnet_name   = "${module.virtual_network.name}"
}

module "gitlab_load_balancer" {
  source = "./load_balancer"

}

#Network interfaces tie together Vms and services. be it public IP or a Load balancer
#This means we need to define the network interfaces after any services (LB's public IPs)
#Then attach the Network interface to a VM later
module "gitlab_network_interface" {
  source      = "./network_interface"

  name        = "${var.name}"
  environment = "${var.environment}"
  stack       = "${var.stack}"
  region      = "${var.region}"
  rg_name     = "${var.rg_name}"
  owner       = "${var.owner}"
  subnet_id   = "${module.subnet.id}"
  lb_backend_pool_id  = "${module.gitlab_load_balancer.lb_backend_pool_id}"
}
