variable "name"           { }
variable "environment"    { }
variable "owner"          { }
variable "stack"          { }
variable "region"         { }

variable "rg_name"        { }
variable "sa_type"        { }
variable "purpose"        { }

module "storage_account" {
  source = "./storage_account"

  name        = "${var.name}"
  environment = "${var.environment}"
  owner       = "${var.owner}"
  stack       = "${var.stack}"
  region      = "${var.region}"
  rg_name     = "${var.rg_name}"

}

module "storage_container" {
  source = "./storage_container"
  
  name        = "${var.name}"
  environment = "${var.environment}"
  stack       = "${var.stack}"
  region      = "${var.region}"
  rg_name     = "${var.rg_name}"
  purpose     = "${var.purpose}"
  sa_name     = "${module.storage_account.name}"

}

output "sa_endpoint"        { value = "${module.storage_account.endpoint}" }
output "sa_container_name"  { value = "${module.storage_container.name}" }
