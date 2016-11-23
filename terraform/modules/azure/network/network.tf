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


module "master_load_balancer" {
  source = "./load_balancer"

  name        = "${var.name}"
  purpose     = "master"
  environment = "${var.environment}"
  stack       = "${var.stack}"
  region      = "${var.region}"
  rg_name     = "${var.rg_name}"
  owner       = "${var.owner}"

	subnet_id   	= "${module.servers_subnet.id}"
	frontend_port	= "443"
	backend_port	= "443"
}

module "master_load_balancer_probe" {
  source = "./load_balancer_probe_http"

  name        = "${var.name}"
  purpose     = "master"
  environment = "${var.environment}"
  stack       = "${var.stack}"
  region      = "${var.region}"
  rg_name     = "${var.rg_name}"
  owner       = "${var.owner}"

  backend_port	= "443"
  probe_path    = "/healthz/ready"
  lb_id         = "${module.master_load_balancer.lb_id}"
}

module "master_load_balancer_rule" {
  source = "./load_balancer_rule"

  name        = "${var.name}"
  purpose     = "master"
  environment = "${var.environment}"
  stack       = "${var.stack}"
  region      = "${var.region}"
  rg_name     = "${var.rg_name}"
  owner       = "${var.owner}"

	frontend_port	= "443"
  backend_port	= "443"
  lb_id         = "${module.master_load_balancer.lb_id}"
  lb_probe_id   = "${module.master_load_balancer_probe.id}"
}

module "node_infra_load_balancer" {
  source = "./load_balancer"

  name        = "${var.name}"
  purpose     = "node_infra"
  environment = "${var.environment}"
  stack       = "${var.stack}"
  region      = "${var.region}"
  rg_name     = "${var.rg_name}"
  owner       = "${var.owner}"

	subnet_id   	= "${module.servers_subnet.id}"
	frontend_port	= "443"
	backend_port	= "443"
}

module "node_infra_load_balancer_probe" {
  source = "./load_balancer_probe_tcp"

  name        = "${var.name}"
  purpose     = "node_infra"
  environment = "${var.environment}"
  stack       = "${var.stack}"
  region      = "${var.region}"
  rg_name     = "${var.rg_name}"
  owner       = "${var.owner}"

  backend_port	= "443"
  lb_id         = "${module.node_infra_load_balancer.lb_id}"
}

module "node_infra_load_balancer_rule" {
  source = "./load_balancer_rule"

  name        = "${var.name}"
  purpose     = "node_infra"
  environment = "${var.environment}"
  stack       = "${var.stack}"
  region      = "${var.region}"
  rg_name     = "${var.rg_name}"
  owner       = "${var.owner}"

	frontend_port	= "443"
  backend_port	= "443"
  lb_id         = "${module.node_infra_load_balancer.lb_id}"
  lb_probe_id   = "${module.node_infra_load_balancer_probe.id}"
}

module "gitlab_load_balancer" {
  source = "./load_balancer"

  name        = "${var.name}"
  purpose     = "gitlab"
  environment = "${var.environment}"
  stack       = "${var.stack}"
  region      = "${var.region}"
  rg_name     = "${var.rg_name}"
  owner       = "${var.owner}"

	subnet_id   	= "${module.servers_subnet.id}"
	frontend_port	= "80"
	backend_port	= "8081"
}

module "gitlab_load_balancer_probe" {
  source = "./load_balancer_probe_http"

  name        = "${var.name}"
  purpose     = "master"
  environment = "${var.environment}"
  stack       = "${var.stack}"
  region      = "${var.region}"
  rg_name     = "${var.rg_name}"
  owner       = "${var.owner}"

	backend_port	= "8081"
  probe_path    = "/users/sign_in"
  lb_id         = "${module.gitlab_load_balancer.lb_id}"
}

module "gitlab_load_balancer_rule" {
  source = "./load_balancer_rule"

  name        = "${var.name}"
  purpose     = "gitlab"
  environment = "${var.environment}"
  stack       = "${var.stack}"
  region      = "${var.region}"
  rg_name     = "${var.rg_name}"
  owner       = "${var.owner}"

	frontend_port	= "443"
  backend_port	= "443"
  lb_id         = "${module.gitlab_load_balancer.lb_id}"
  lb_probe_id   = "${module.gitlab_load_balancer_probe.id}"
}

#Network interfaces tie together Vms and services. be it public IP or a Load balancer
#This means we need to define the network interfaces after any services (LB's public IPs)
#Then attach the Network interface to a VM later

module "gitlab_network_interface_lb" {
  source      = "./network_interface_lb"

  name        = "${var.name}"
  environment = "${var.environment}"
  stack       = "${var.stack}"
  region      = "${var.region}"
  rg_name     = "${var.rg_name}"
  owner       = "${var.owner}"
  subnet_id   = "${module.servers_subnet.id}"
  lb_backend_pool_id  = "${module.gitlab_load_balancer.lb_backend_pool_id}"
  purpose     = "gitlab"
}


module "master_network_interface_lb" {
  source      = "./network_interface_lb"

  name        = "${var.name}"
  environment = "${var.environment}"
  stack       = "${var.stack}"
  region      = "${var.region}"
  rg_name     = "${var.rg_name}"
  owner       = "${var.owner}"
  subnet_id   = "${module.servers_subnet.id}"
  lb_backend_pool_id  = "${module.master_load_balancer.lb_backend_pool_id}"
  purpose     = "master"
}

module "node_infra_network_interface_lb" {
  source      = "./network_interface_lb"

  name        = "${var.name}"
  environment = "${var.environment}"
  stack       = "${var.stack}"
  region      = "${var.region}"
  rg_name     = "${var.rg_name}"
  owner       = "${var.owner}"
  subnet_id   = "${module.servers_subnet.id}"
  lb_backend_pool_id  = "${module.node_infra_load_balancer.lb_backend_pool_id}"
  purpose     = "node-infra"
}

module "node_worker_network_interface" {
  source      = "./network_interface"

  name        = "${var.name}"
  environment = "${var.environment}"
  stack       = "${var.stack}"
  region      = "${var.region}"
  rg_name     = "${var.rg_name}"
  owner       = "${var.owner}"
  subnet_id   = "${module.servers_subnet.id}"
  purpose     = "node-worker"
}

module "storage_network_interface" {
  source      = "./network_interface"

  name        = "${var.name}"
  environment = "${var.environment}"
  stack       = "${var.stack}"
  region      = "${var.region}"
  rg_name     = "${var.rg_name}"
  owner       = "${var.owner}"
  subnet_id   = "${module.servers_subnet.id}"
  purpose     = "storage"
}

module "formation_network_interface" {
  source      = "./network_interface"

  name        = "${var.name}"
  environment = "${var.environment}"
  stack       = "${var.stack}"
  region      = "${var.region}"
  rg_name     = "${var.rg_name}"
  owner       = "${var.owner}"
  subnet_id   = "${module.servers_subnet.id}"
  purpose     = "formation"
}

# Outputs

output "gitlab_network_interface_id"        { value = "${module.gitlab_network_interface_lb.id}"}
output "master_network_interface_id"        { value = "${module.master_network_interface_lb.id}"}
output "node_infra_network_interface_id"    { value = "${module.node_infra_network_interface_lb.id}"}
output "node_worker_network_interface_id"   { value = "${module.node_worker_network_interface.id}"}
output "formation_network_interface_id"     { value = "${module.formation_network_interface.id}"}
output "storage_network_interface_id"       { value = "${module.storage_network_interface.id}"}
