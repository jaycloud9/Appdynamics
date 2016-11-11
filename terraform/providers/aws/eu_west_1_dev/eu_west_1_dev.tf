variable "name"              { }
variable "region"            { }
variable "sub_domain"        { }

variable "vpc_cidr"        { }
variable "azs"             { }
variable "private_subnets" { }
variable "public_subnets"  { }

variable "haproxy_node_count"    { }
variable "haproxy_instance_type" { }
variable "haproxy_artifact_name" { }
variable "haproxy_artifacts"     { }

provider "aws" {
  region = "${var.region}"
}

resource "aws_key_pair" "site_key" {
  key_name   = "${var.key_pair_name}"
  public_key = "${var.key_public_key}"

  lifecycle { create_before_destroy = true }
}

module "network" {
  source = "../../../modules/aws/network"

  name            = "${var.name}"
  vpc_cidr        = "${var.vpc_cidr}"
  azs             = "${var.azs}"
  region          = "${var.region}"
  private_subnets = "${var.private_subnets}"
  public_subnets  = "${var.public_subnets}"
  ssl_cert        = "${var.site_ssl_cert}"
  ssl_key         = "${var.site_ssl_key}"
  key_name        = "${aws_key_pair.site_key.key_name}"
  private_key     = "${var.site_private_key}"
  sub_domain      = "${var.sub_domain}"
  route_zone_id   = "${terraform_remote_state.aws_global.output.zone_id}"

}

module "compute" {
  source = "../../../modules/aws/compute"

  name               = "${var.name}"
  region             = "${var.region}"
  vpc_id             = "${module.network.vpc_id}"
  vpc_cidr           = "${var.vpc_cidr}"
  key_name           = "${aws_key_pair.site_key.key_name}"
  azs                = "${var.azs}"
  public_subnet_ids  = "${module.network.public_subnet_ids}"
  sub_domain         = "${var.sub_domain}"
}
