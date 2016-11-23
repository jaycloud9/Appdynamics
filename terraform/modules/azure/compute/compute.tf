variable "name"           { }
variable "environment"    { }
variable "owner"          { }
variable "stack"          { }
variable "region"         { }
variable "rg_name"        { }

variable "vm_size"        { }
variable "os_storage_container" { }
variable "tf_admin_password"    { }
variable "tf_user"        { }
variable "public_key"     { }

variable "gitlab_network_inf"       { }
variable "master_network_inf"       { }
variable "node_infra_network_inf"   { }
variable "node_worker_network_inf"  { }
variable "storage_network_inf"      { }
variable "formation_network_inf"    { }


module "gitlab" {
  source = "./rhel7"
  
  name                = "${var.name}"
  environment         = "${var.environment}"
  stack               = "${var.stack}"
  rg_name             = "${var.rg_name}"
  owner               = "${var.owner}" 
  region              = "${var.region}"

  network_inf         = "${var.gitlab_network_inf}"
  vm_size             = "${var.vm_size}"
  os_storage_container= "${var.os_storage_container}"
  tf_admin_passwd     = "${var.tf_admin_password}"
  tf_user             = "${var.tf_user}"
  public_key          = "${var.public_key}"
  type                = "gitlab"

}

module "openshift_master" {
  source = "./rhel7"
  
  name                = "${var.name}"
  environment         = "${var.environment}"
  stack               = "${var.stack}"
  rg_name             = "${var.rg_name}"
  owner               = "${var.owner}" 
  region              = "${var.region}"

  network_inf         = "${var.master_network_inf}"
  vm_size             = "${var.vm_size}"
  os_storage_container= "${var.os_storage_container}"
  tf_admin_passwd     = "${var.tf_admin_password}"
  tf_user             = "${var.tf_user}"
  public_key          = "${var.public_key}"
  type                = "master"

}

module "openshift_node_infra" {
  source = "./rhel7"
  
  name                = "${var.name}"
  environment         = "${var.environment}"
  stack               = "${var.stack}"
  rg_name             = "${var.rg_name}"
  owner               = "${var.owner}" 
  region              = "${var.region}"

  network_inf         = "${var.node_infra_network_inf}"
  vm_size             = "${var.vm_size}"
  os_storage_container= "${var.os_storage_container}"
  tf_admin_passwd     = "${var.tf_admin_password}"
  tf_user             = "${var.tf_user}"
  public_key          = "${var.public_key}"
  type                = "node-infra"

}

module "formation" {
  source = "./rhel7"
  
  name                = "${var.name}"
  environment         = "${var.environment}"
  stack               = "${var.stack}"
  rg_name             = "${var.rg_name}"
  owner               = "${var.owner}" 
  region              = "${var.region}"

  network_inf         = "${var.formation_network_inf}"
  vm_size             = "${var.vm_size}"
  os_storage_container= "${var.os_storage_container}"
  tf_admin_passwd     = "${var.tf_admin_password}"
  tf_user             = "${var.tf_user}"
  public_key          = "${var.public_key}"
  type                = "formation"

}

module "storage" {
  source = "./rhel7"
  
  name                = "${var.name}"
  environment         = "${var.environment}"
  stack               = "${var.stack}"
  rg_name             = "${var.rg_name}"
  owner               = "${var.owner}" 
  region              = "${var.region}"

  network_inf         = "${var.storage_network_inf}"
  vm_size             = "${var.vm_size}"
  os_storage_container= "${var.os_storage_container}"
  tf_admin_passwd     = "${var.tf_admin_password}"
  tf_user             = "${var.tf_user}"
  public_key          = "${var.public_key}"
  type                = "storage"

}

module "openshift_node_worker" {
  source = "./rhel7"
  
  name                = "${var.name}"
  environment         = "${var.environment}"
  stack               = "${var.stack}"
  rg_name             = "${var.rg_name}"
  owner               = "${var.owner}" 
  region              = "${var.region}"

  network_inf         = "${var.node_worker_network_inf}"
  vm_size             = "${var.vm_size}"
  os_storage_container= "${var.os_storage_container}"
  tf_admin_passwd     = "${var.tf_admin_password}"
  tf_user             = "${var.tf_user}"
  public_key          = "${var.public_key}"
  type                = "node-worker"
}
