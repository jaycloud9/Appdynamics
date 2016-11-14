#--------------------------------------------------------------
# This module creates all resources necessary for the
# gitlab application
#--------------------------------------------------------------

variable "name"                	{ default = "gitlab" }
variable "vpc_id"               { }
variable "count"								{	default = 1 }
variable "aws_key_name"					{ }
variable "domain"								{ }
variable "ami"									{ }
variable "size"									{ default = "t2.large" }
variable "subnet_ids"    				{ }
variable "local_subnets"        { }
variable "ebs_disk_mount"				{ default = "/dev/sdh"}
variable "ebs_disk_size"				{ default = 200}
variable "ssl_certificate_id"		{ }


resource "aws_security_group" "allow_instance_access" {
  name = "${var.name}.allow_instance_access"
  vpc_id = "${var.vpc_id}"
  description = "Allow Instance access"
 ingress {
    from_port = 8081
    to_port = 8081
    protocol = "tcp"
    cidr_blocks = ["${element(split(",", var.local_subnets), count.index)}"]
  }
  
 ingress {
    from_port = 22
    to_port = 22
    protocol = "tcp"
    cidr_blocks = [
			"80.169.34.194/32",
      "5.80.40.141/32"
    ]

  }

  egress {
    from_port = 0
    to_port = 0
    protocol = "-1"
    cidr_blocks = [
      "0.0.0.0/0"
		]
  }

}

resource "aws_security_group" "allow_restricted_http_and_https_elb" {
  name = "${var.name}.allow_restricted_http_and_https_elb"
  vpc_id = "${var.vpc_id}"
  description = "Allow restricted https incoming access for ELB"
  ingress {
    from_port = 80
    to_port = 80
    protocol = "tcp"
    cidr_blocks = [
      "80.169.34.194/32",
      "5.80.40.141/32"
		]
  }

  ingress {
    from_port = 443
    to_port = 443
    protocol = "tcp"
    cidr_blocks = [
      "80.169.34.194/32",
      "5.80.40.141/32"
		]
  }
  egress {
    from_port = 8081
    to_port = 8081
    protocol = "tcp"
    cidr_blocks = [
      "10.0.0.0/16"]
  }
}


resource "aws_instance" "instance" {
  count = "${var.count}"
  key_name = "${var.aws_key_name}"
  tags {
    Name = "${var.name}-${count.index + 1}"
    Type = "gitlab"
  }
  ami = "${var.ami}"
  instance_type = "${var.size}"
  subnet_id = "${element(split(",", var.subnet_ids), count.index)}"
  ebs_block_device {
    device_name = "${var.ebs_disk_mount}"
    volume_size = "${var.ebs_disk_size}"
  }
  vpc_security_group_ids = [
    "${aws_security_group.allow_instance_access.id}"
	]
}

resource "aws_elb" "elb" {
  name = "${var.name}-elb"
  listener {
    instance_port = 8081
    instance_protocol = "http"
    lb_port = 443
    lb_protocol = "https"
    ssl_certificate_id = "${var.ssl_certificate_id}"
  }
  health_check {
    healthy_threshold = 2
    unhealthy_threshold = 2
    timeout = 3
    target = "HTTP:8081/users/sign_in"
    interval = 30
  }
  connection_draining = true
  instances = [
    "${aws_instance.instance.*.id}"]
  security_groups = [
    "${aws_security_group.allow_restricted_http_and_https_elb.id}"]
  subnets = ["${split(",", var.subnet_ids)}"]
}

resource "aws_lb_cookie_stickiness_policy" "elb_sticky" {
    name = "${var.name}-elb-sticky-policy"
    load_balancer = "${aws_elb.elb.id}"
    lb_port = 443
    cookie_expiration_period = 600
}

resource "aws_route53_record" "external_route53_zone" {
	name = "external_${var.name}_route53"
  zone_id = "Z1DHMGOFTZGBIQ"
  name = "${var.name}.${var.domain}"
  type = "CNAME"
  ttl = "30"
  records = ["${aws_elb.elb.dns_name}"]
}

