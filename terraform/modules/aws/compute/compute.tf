#--------------------------------------------------------------
# This module creates all compute resources
#--------------------------------------------------------------

variable "name"                 { }
variable "region"               { }
variable "aws_key_name"         { }
variable "domain"               { }
variable "ami"                  { }
variable "size"                 { }
variable "public_subnet_id"     { }
variable "local_subnets"        { }
variable "ebs_disk_mount"       { }
variable "ebs_disk_size"        { }
variable "ssl_certificate_id"   { }



module "gitlab" {
  source                = "./gitlab"
  name                  = "${var.name}-gitlab"
  aws_key_name          = "${var.aws_key_name}"
  domain                = "${var.domain}"
  ami                   = "${var.ami}"
  size                  = "${var.size}"
  subnet_id             = "${var.public_subnet_id}"
  local_subnets         = "${var.local_subnets}"
  ebs_disk_mount        = "${var.ebs_disk_mount}"
  ebs_disk_size         = "${var.ebs_disk_size}"
  ssl_certificate_id    = "${var.ssl_certificate_id}"
}
