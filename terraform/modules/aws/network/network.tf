#--------------------------------------------------------------
# This module creates all networking resources
#--------------------------------------------------------------

variable "name"            { }
variable "vpc_cidr"        { }
variable "azs"             { }
variable "public_subnets"  { }
variable "key_name"        { }
variable "private_key"     { }

module "vpc" {
  source = "./vpc"

  name = "${var.name}-vpc"
  cidr = "${var.vpc_cidr}"
}

module "public_subnet" {
  source = "./public_subnet"

  name   = "${var.name}-public"
  vpc_id = "${module.vpc.vpc_id}"
  cidrs  = "${var.public_subnets}"
  azs    = "${var.azs}"
}
