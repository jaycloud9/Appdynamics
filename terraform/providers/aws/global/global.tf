variable "domain"       { }
variable "name"         { }
variable "region"       { }


provider "aws" {
  region = "${var.region}"
}
}
