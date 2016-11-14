#--------------------------------------------------------------
# This module creates all compute resources
#--------------------------------------------------------------

variable "name"                 { }
variable "region"               { }
variable "aws_key_name"         { }
variable "vpc_id"               { }
variable "domain"               { }
variable "ami"                  { }
variable "public_subnet_ids"    { }
variable "local_subnets"        { }
variable "ssl_certificate_id"   { }



module "gitlab" {
  source                = "./gitlab"
  name                  = "${var.name}-gitlab"
  vpc_id                = "${var.vpc_id}"
  aws_key_name          = "${var.aws_key_name}"
  domain                = "${var.domain}"
  ami                   = "${var.ami}"
  subnet_ids            = "${var.public_subnet_ids}"
  local_subnets         = "${var.local_subnets}"
  ssl_certificate_id    = "${var.ssl_certificate_id}"
}
