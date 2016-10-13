provider "aws" {
  region = "eu-west-1"
}

resource "aws_key_pair" "tc_key_pair" {
  key_name = "tc_key_pair"
  public_key = "${file("keys/tc_key.pub")}"
}

resource "aws_vpc" "tc_vpc" {
  cidr_block = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support = true
}

resource "aws_subnet" "tc_subnet" {
  vpc_id = "${aws_vpc.tc_vpc.id}"
  cidr_block = "10.0.0.0/24"
  map_public_ip_on_launch = true
}

resource "aws_internet_gateway" "tc_internet_gateway" {
  vpc_id = "${aws_vpc.tc_vpc.id}"
}

resource "aws_route_table" "tc_route_table" {
  vpc_id = "${aws_vpc.tc_vpc.id}"
}

resource "aws_main_route_table_association" "tc_main_router_table_association" {
  vpc_id = "${aws_vpc.tc_vpc.id}"
  route_table_id = "${aws_route_table.tc_route_table.id}"
}

resource "aws_route" "tc_gateway_route" {
  route_table_id = "${aws_route_table.tc_route_table.id}"
  destination_cidr_block = "0.0.0.0/0"
  gateway_id = "${aws_internet_gateway.tc_internet_gateway.id}"
}

resource "aws_security_group" "tc_allow_all_outgoing_security_group" {
  name = "tc_allow_all_outgoing_security_group"
  description = "Allow all outgoing access"
  egress {
    from_port = 0
    to_port = 0
    protocol = "-1"
    cidr_blocks = [
      "0.0.0.0/0"]
  }
}

resource "aws_security_group" "tc_allow_restricted_ssh_incoming_security_group" {
  name = "tc_allow_restricted_ssh_incoming_security_group"
  description = "Allow restricted ssh incoming access"
  ingress {
    from_port = 22
    to_port = 22
    protocol = "tcp"
    cidr_blocks = [
      "80.169.34.194/32"]
  }
}

resource "aws_security_group" "tc_allow_restricted_https_incoming_security_group" {
  name = "tc_allow_restricted_https_incoming_security_group"
  description = "Allow restricted https incoming access"
  ingress {
    from_port = 443
    to_port = 443
    protocol = "https"
    cidr_blocks = [
      "80.169.34.194/32"]
  }
}

resource "aws_security_group" "tc_allow_local_all_incoming_security_group" {
  name = "tc_allow_local_all_incoming_security_group"
  description = "Allow local all incoming access"
  ingress {
    from_port = 0
    to_port = 0
    protocol = "-1"
    cidr_blocks = [
      "10.0.0.0/24"]
  }
}

resource "aws_instance" "tc_master_instance" {
  count = 3
  tags {
    Name = "tc-master-instance-${count.index + 1}"
    Type = "tc-master-instance"
  }
  ami = "ami-8b8c57f8"
  instance_type = "t2.large"
  subnet_id = "${aws_subnet.tc_subnet.id}"
  vpc_security_group_ids = [
    "${aws_security_group.tc_allow_all_outgoing_security_group.id}",
    "${aws_security_group.tc_allow_restricted_ssh_incoming_security_group.id}",
    "${aws_security_group.tc_allow_local_all_incoming_security_group.id}"]
}

resource "aws_instance" "tc_registry_instance" {
  count = 1
  tags {
    Name = "tc-registry-instance-${count.index + 1}"
    Type = "tc-registry-instance"
  }
  ami = "ami-8b8c57f8"
  instance_type = "c3.4xlarge"
  subnet_id = "${aws_subnet.tc_subnet.id}"
  vpc_security_group_ids = [
    "${aws_security_group.tc_allow_all_outgoing_security_group.id}",
    "${aws_security_group.tc_allow_restricted_ssh_incoming_security_group.id}",
    "${aws_security_group.tc_allow_local_all_incoming_security_group.id}"]
}

resource "aws_instance" "tc_router_instance" {
  count = 2
  tags {
    Name = "tc-router-instance-${count.index + 1}"
    Type = "tc-router-instance"
  }
  ami = "ami-8b8c57f8"
  instance_type = "t2.medium"
  subnet_id = "${aws_subnet.tc_subnet.id}"
  vpc_security_group_ids = [
    "${aws_security_group.tc_allow_all_outgoing_security_group.id}",
    "${aws_security_group.tc_allow_restricted_ssh_incoming_security_group.id}",
    "${aws_security_group.tc_allow_local_all_incoming_security_group.id}"]
}

resource "aws_instance" "tc_controller_instance" {
  count = 3
  tags {
    Name = "tc-controller-instance-${count.index + 1}"
    Type = "tc-controller-instance"
  }
  ami = "ami-8b8c57f8"
  instance_type = "c3.4xlarge"
  subnet_id = "${aws_subnet.tc_subnet.id}"
  vpc_security_group_ids = [
    "${aws_security_group.tc_allow_all_outgoing_security_group.id}",
    "${aws_security_group.tc_allow_restricted_ssh_incoming_security_group.id}",
    "${aws_security_group.tc_allow_local_all_incoming_security_group.id}"]
}

resource "aws_instance" "tc_formation_instance" {
  count = 1
  tags {
    Name = "tc-formation-instance-${count.index + 1}"
    Type = "tc-formation-instance"
  }
  ami = "ami-8b8c57f8"
  instance_type = "t2.small"
  subnet_id = "${aws_subnet.tc_subnet.id}"
  vpc_security_group_ids = [
    "${aws_security_group.tc_allow_all_outgoing_security_group.id}",
    "${aws_security_group.tc_allow_restricted_ssh_incoming_security_group.id}",
    "${aws_security_group.tc_allow_local_all_incoming_security_group.id}"]
}

resource "aws_elb" "tc_master_instances_elb" {
  name = "tc-master-instances-elb"
  availability_zones = [
    "eu-west-1a"]
  listener {
    instance_port = 8080
    instance_protocol = "http"
    lb_port = 443
    lb_protocol = "https"
    ssl_certificate_id = ""
  }
  health_check {
    healthy_threshold = 2
    unhealthy_threshold = 2
    timeout = 3
    target = "HTTP:8080/"
    interval = 30
  }
  idle_timeout = 400
  connection_draining = true
  connection_draining_timeout = 400
  instances = [
    "${aws_instance.tc_master_instance.*.id}"]
  security_groups = [
    "${aws_security_group.tc_allow_restricted_https_incoming_security_group.id}"]
}

resource "aws_elb" "tc_router_instances_elb" {
  name = "tc-router-instances-elb"
  availability_zones = [
    "eu-west-1a"]
  listener {
    instance_port = 8080
    instance_protocol = "http"
    lb_port = 80
    lb_protocol = "http"
  }
  listener {
    instance_port = 8080
    instance_protocol = "http"
    lb_port = 443
    lb_protocol = "https"
    ssl_certificate_id = ""
  }
  health_check {
    healthy_threshold = 2
    unhealthy_threshold = 2
    timeout = 3
    target = "HTTP:8080/"
    interval = 30
  }
  idle_timeout = 400
  connection_draining = true
  connection_draining_timeout = 400
  instances = [
    "${aws_instance.tc_router_instance.*.id}"]
  security_groups = [
    "${aws_security_group.tc_allow_restricted_https_incoming_security_group.id}"]
}

resource "aws_route53_zone" "tc_local_route53_zone" {
  name = "temenos.local"
  vpc_id = "${aws_vpc.tc_vpc.id}"
}

resource "aws_route53_zone" "tc_external_route53_zone" {
  name = "temenos.cloud"
}

resource "aws_route53_record" "tc_external_router_route53_zone" {
  zone_id = "${aws_route53_zone.tc_external_route53_zone.id}"
  name = "cluster1.${aws_route53_zone.tc_external_route53_zone.name}"
  type = "CNAME"
  ttl = "30"
  records = ["${aws_elb.tc_router_instances_elb.dns_name}"]
}

resource "aws_route53_record" "tc_external_master_route53_zone" {
  zone_id = "${aws_route53_zone.tc_external_route53_zone.id}"
  name = "*.apps.cluster1.${aws_route53_zone.tc_external_route53_zone.name}"
  type = "CNAME"
  ttl = "30"
  records = ["${aws_elb.tc_master_instances_elb.dns_name}"]
}