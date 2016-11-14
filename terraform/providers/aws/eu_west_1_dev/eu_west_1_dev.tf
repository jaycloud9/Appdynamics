variable "name"               { }
variable "region"             { }
variable "domain"             { }
variable "key_pair_name"      { }

variable "vpc_cidr"           { }
variable "azs"                { }
variable "public_subnets"     { }

variable "ami"                { }
variable "ssl_certificate_id" { }

provider "aws" {
  region = "${var.region}"
}

resource "aws_key_pair" "site_key" {
  key_name   = "${var.key_pair_name}"
  public_key = "${file("../../../../keys/key.pub")}"

  lifecycle { create_before_destroy = true }
}

module "network" {
  source = "../../../modules/aws/network"

  name            = "${var.name}"
  vpc_cidr        = "${var.vpc_cidr}"
  azs             = "${var.azs}"
  public_subnets  = "${var.public_subnets}"

}

module "compute" {
  source = "../../../modules/aws/compute"

  name                = "${var.name}"
  ami                 = "${var.ami}"
  region              = "${var.region}"
  vpc_id              = "${module.network.vpc_id}"
  aws_key_name        = "${aws_key_pair.site_key.key_name}"
  public_subnet_ids   = "${module.network.public_subnet_ids}"
  local_subnets       = "${module.network.public_subnet_addresses}"
  domain              = "${var.domain}"
  ssl_certificate_id  = "${var.ssl_certificate_id}"
}
