provider "aws" {
  region = "eu-west-1"
}

resource "aws_vpc" "tc_vpc" {
  cidr_block = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support = true
}

resource "aws_subnet" "tc_subnet" {
  vpc_id = "${aws_vpc.tc_vpc.id}"
  cidr_block = "10.0.0.0/24"
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
    Name = "tc_master_instance-${count.index + 1}"
    Type = "tc_master_instance"
  }
  ami = "ami-8b8c57f8"
  instance_type = "t2.large"
  subnet_id = "${aws_subnet.tc_subnet.id}"
  vpc_security_group_ids = [
    "${aws_security_group.tc_allow_all_outgoing_security_group}",
    "${aws_security_group.tc_allow_restricted_ssh_incoming_security_group}",
    "${aws_security_group.tc_allow_local_all_incoming_security_group}"]
}

resource "aws_instance" "tc_registry_instance" {
  count = 1
  tags {
    Name = "tc_registry_instance-${count.index + 1}"
    Type = "tc_registry_instance"
  }
  ami = "ami-8b8c57f8"
  instance_type = "c3.4xlarge"
  subnet_id = "${aws_subnet.tc_subnet.id}"
  vpc_security_group_ids = [
    "${aws_security_group.tc_allow_all_outgoing_security_group}",
    "${aws_security_group.tc_allow_restricted_ssh_incoming_security_group}",
    "${aws_security_group.tc_allow_local_all_incoming_security_group}"]
}

resource "aws_instance" "tc_router_instance" {
  count = 2
  tags {
    Name = "tc_router_instance-${count.index + 1}"
    Type = "tc_router_instance"
  }
  ami = "ami-8b8c57f8"
  instance_type = "t2.medium"
  subnet_id = "${aws_subnet.tc_subnet.id}"
  vpc_security_group_ids = [
    "${aws_security_group.tc_allow_all_outgoing_security_group}",
    "${aws_security_group.tc_allow_restricted_ssh_incoming_security_group}",
    "${aws_security_group.tc_allow_local_all_incoming_security_group}"]
}

resource "aws_instance" "tc_controller_instance" {
  count = 3
  tags {
    Name = "tc_controller_instance-${count.index + 1}"
    Type = "tc_controller_instance"
  }
  ami = "ami-8b8c57f8"
  instance_type = "c3.4xlarge"
  subnet_id = "${aws_subnet.tc_subnet.id}"
  vpc_security_group_ids = [
    "${aws_security_group.tc_allow_all_outgoing_security_group}",
    "${aws_security_group.tc_allow_restricted_ssh_incoming_security_group}",
    "${aws_security_group.tc_allow_local_all_incoming_security_group}"]
}

resource "aws_instance" "tc_formation_instance" {
  count = 1
  tags {
    Name = "tc_formation_instance-${count.index + 1}"
    Type = "tc_formation_instance"
  }
  ami = "ami-8b8c57f8"
  instance_type = "t2.small"
  subnet_id = "${aws_subnet.tc_subnet.id}"
  vpc_security_group_ids = [
    "${aws_security_group.tc_allow_all_outgoing_security_group}",
    "${aws_security_group.tc_allow_restricted_ssh_incoming_security_group}",
    "${aws_security_group.tc_allow_local_all_incoming_security_group}"]
}

resource "aws_elb" "tc_master_instances_elb" {
  name = "tc_master_instances_elb"
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
    "${aws_instance.tc_master_instance}}"]
  security_groups = [
    "${aws_security_group.tc_allow_restricted_https_incoming_security_group}"]
}

resource "aws_elb" "tc_router_instances_elb" {
  name = "tc_router_instances_elb"
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
    "${aws_instance.tc_router_instance}}"]
  security_groups = [
    "${aws_security_group.tc_allow_restricted_https_incoming_security_group}"]
}

resource "aws_route53_zone" "tc_local_route53_zone" {
  name = "temenos.local"
  vpc_id = "${aws_vpc.tc_vpc.id}"
}