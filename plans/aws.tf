provider "aws" {
  region = "eu-west-1"
}

resource "aws_key_pair" "key_pair" {
  key_name = "key_pair"
  public_key = "${file("keys/key.pub")}"
}

resource "aws_vpc" "vpc" {
  cidr_block = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support = true
}

resource "aws_subnet" "subnetA" {
  vpc_id = "${aws_vpc.vpc.id}"
  availability_zone = "eu-west-1a"
  cidr_block = "10.0.0.0/24"
  map_public_ip_on_launch = true
}

resource "aws_internet_gateway" "internet_gateway" {
  vpc_id = "${aws_vpc.vpc.id}"
}

resource "aws_route_table" "route_table" {
  vpc_id = "${aws_vpc.vpc.id}"
}

resource "aws_main_route_table_association" "main_router_table_association" {
  vpc_id = "${aws_vpc.vpc.id}"
  route_table_id = "${aws_route_table.route_table.id}"
}

resource "aws_route" "gateway_route" {
  route_table_id = "${aws_route_table.route_table.id}"
  destination_cidr_block = "0.0.0.0/0"
  gateway_id = "${aws_internet_gateway.internet_gateway.id}"
}

resource "aws_security_group" "allow_all_outgoing_security_group" {
  name = "allow_all_outgoing_security_group"
  vpc_id = "${aws_vpc.vpc.id}"
  description = "Allow all outgoing access"
  egress {
    from_port = 0
    to_port = 0
    protocol = "-1"
    cidr_blocks = [
      "0.0.0.0/0"]
  }
}

resource "aws_security_group" "allow_restricted_ssh_incoming_security_group" {
  name = "allow_restricted_ssh_incoming_security_group"
  vpc_id = "${aws_vpc.vpc.id}"
  description = "Allow restricted ssh incoming access"
  ingress {
    from_port = 22
    to_port = 22
    protocol = "tcp"
    cidr_blocks = [
      "80.169.34.194/32",
      "5.80.40.141/32"]
  }
}

resource "aws_security_group" "allow_restricted_http_and_https_elb" {
  name = "allow_restricted_http_and_https_elb"
  vpc_id = "${aws_vpc.vpc.id}"
  description = "Allow restricted https incoming access for ELB"
  ingress {
    from_port = 80
    to_port = 80
    protocol = "tcp"
    cidr_blocks = [
      "80.169.34.194/32",
      "5.80.40.141/32",
      "${aws_instance.master_instance.public_ip}/32",
      "${aws_instance.node_worker_instance.public_ip}/32",
      "${aws_instance.node_infra_instance.public_ip}/32"]
  }
  
  ingress {
    from_port = 443
    to_port = 443
    protocol = "tcp"
    cidr_blocks = [
      "80.169.34.194/32",
      "5.80.40.141/32",
      "${aws_instance.master_instance.public_ip}/32",
      "${aws_instance.node_worker_instance.public_ip}/32",
      "${aws_instance.node_infra_instance.public_ip}/32"]
  }
  
  egress {
    from_port = 80
    to_port = 80
    protocol = "tcp"
    cidr_blocks = [
      "10.0.0.0/24"]
  }
  egress {
    from_port = 8081
    to_port = 8081
    protocol = "tcp"
    cidr_blocks = [
      "10.0.0.0/24"]
  }
  egress {
    from_port = 443
    to_port = 443
    protocol = "tcp"
    cidr_blocks = [
      "10.0.0.0/24"]
  }
}

resource "aws_security_group" "allow_restricted_https_incoming_security_group" {
  name = "allow_restricted_https_incoming_security_group"
  vpc_id = "${aws_vpc.vpc.id}"
  description = "Allow restricted https incoming access"
  ingress {
    from_port = 443
    to_port = 443
    protocol = "tcp"
    cidr_blocks = [
      "80.169.34.194/32",
      "5.80.40.141/32"]
  }
}

resource "aws_security_group" "allow_restricted_http_incoming_security_group" {
  name = "allow_restricted_http_incoming_security_group"
  vpc_id = "${aws_vpc.vpc.id}"
  description = "Allow restricted http incoming access"
  ingress {
    from_port = 80  
    to_port = 80
    protocol = "tcp"
    cidr_blocks = [
      "80.169.34.194/32",
      "5.80.40.141/32"]
  }
}

resource "aws_security_group" "allow_local_all_incoming_security_group" {
  name = "allow_local_all_incoming_security_group"
  vpc_id = "${aws_vpc.vpc.id}"
  description = "Allow local all incoming access"
  ingress {
    from_port = 0
    to_port = 0
    protocol = "-1"
    cidr_blocks = [
      "10.0.0.0/24"]
  }
}

resource "aws_instance" "gitlab_instance" {
  count = 1
  key_name = "${aws_key_pair.key_pair.key_name}"
  tags {
    Name = "gitlab-${count.index + 1}"
    Type = "gitlab"
  }
  ami = "ami-8b8c57f8"
  instance_type = "t2.large"
  subnet_id = "${aws_subnet.subnetA.id}"
  vpc_security_group_ids = [
    "${aws_security_group.allow_all_outgoing_security_group.id}",
    "${aws_security_group.allow_restricted_ssh_incoming_security_group.id}",
    "${aws_security_group.allow_restricted_http_incoming_security_group.id}",
    "${aws_security_group.allow_local_all_incoming_security_group.id}"]
}

resource "aws_instance" "formation_instance" {
  count = 1
  key_name = "${aws_key_pair.key_pair.key_name}"
  tags {
    Name = "formation-${count.index + 1}"
    Type = "formation"
  }
  ami = "ami-8b8c57f8"
  instance_type = "t2.large"
  subnet_id = "${aws_subnet.subnetA.id}"
  vpc_security_group_ids = [
    "${aws_security_group.allow_all_outgoing_security_group.id}",
    "${aws_security_group.allow_restricted_ssh_incoming_security_group.id}",
    "${aws_security_group.allow_local_all_incoming_security_group.id}"]
}

resource "aws_instance" "master_instance" {
  count = 1
  key_name = "${aws_key_pair.key_pair.key_name}"
  tags {
    Name = "master-${count.index + 1}"
    Type = "master"
    Docker = "true"
    SubType = "storage"
  }
  ami = "ami-8b8c57f8"
  instance_type = "t2.large"
  subnet_id = "${aws_subnet.subnetA.id}"
  vpc_security_group_ids = [
    "${aws_security_group.allow_all_outgoing_security_group.id}",
    "${aws_security_group.allow_restricted_ssh_incoming_security_group.id}",
    "${aws_security_group.allow_local_all_incoming_security_group.id}"]
}

resource "aws_instance" "node_infra_instance" {
  count = 1
  key_name = "${aws_key_pair.key_pair.key_name}"
  tags {
    Name = "node-infra-${count.index + 1}"
    Type = "node-infra"
    Docker = "true"
  }
  ami = "ami-8b8c57f8"
  instance_type = "t2.large"
  subnet_id = "${aws_subnet.subnetA.id}"
  vpc_security_group_ids = [
    "${aws_security_group.allow_all_outgoing_security_group.id}",
    "${aws_security_group.allow_restricted_ssh_incoming_security_group.id}",
    "${aws_security_group.allow_local_all_incoming_security_group.id}"]
}

resource "aws_instance" "node_worker_instance" {
  count = 1
  key_name = "${aws_key_pair.key_pair.key_name}"
  tags {
    Name = "node-worker-${count.index + 1}"
    Type = "node-worker"
    Docker = "true"
  }
  ami = "ami-8b8c57f8"
  instance_type = "t2.large"
  subnet_id = "${aws_subnet.subnetA.id}"
  vpc_security_group_ids = [
    "${aws_security_group.allow_all_outgoing_security_group.id}",
    "${aws_security_group.allow_restricted_ssh_incoming_security_group.id}",
    "${aws_security_group.allow_local_all_incoming_security_group.id}"]
}

# Find a better way to attach disks to every host...
resource "aws_ebs_volume" "gitlab" {
  availability_zone = "eu-west-1a"
  size = 200
}

resource "aws_ebs_volume" "master" {
  availability_zone = "eu-west-1a"
  size = 200
}

resource "aws_ebs_volume" "node_worker" {
  availability_zone = "eu-west-1a"
  size = 200
}

resource "aws_ebs_volume" "node_infra" {
  availability_zone = "eu-west-1a"
  size = 200
}

resource "aws_ebs_volume" "formation" {
  availability_zone = "eu-west-1a"
  size = 200
}

resource "aws_volume_attachment" "ebs_att_formation" {
  device_name = "/dev/sdh"
  volume_id = "${aws_ebs_volume.formation.id}"
  instance_id = "${aws_instance.formation_instance.id}"
}

resource "aws_volume_attachment" "ebs_att_gitlab" {
  device_name = "/dev/sdh"
  volume_id = "${aws_ebs_volume.gitlab.id}"
  instance_id = "${aws_instance.gitlab_instance.id}"
}

resource "aws_volume_attachment" "ebs_att_master" {
  device_name = "/dev/sdh"
  volume_id = "${aws_ebs_volume.master.id}"
  instance_id = "${aws_instance.master_instance.id}"
}

resource "aws_volume_attachment" "ebs_att_node_worker" {
  device_name = "/dev/sdh"
  volume_id = "${aws_ebs_volume.node_worker.id}"
  instance_id = "${aws_instance.node_worker_instance.id}"
}

resource "aws_volume_attachment" "ebs_att_node_infra" {
  device_name = "/dev/sdh"
  volume_id = "${aws_ebs_volume.node_infra.id}"
  instance_id = "${aws_instance.node_infra_instance.id}"
}

resource "aws_elb" "master_elb" {
  name = "master-elb"
  listener {
    instance_port = 443
    instance_protocol = "https"
    lb_port = 443
    lb_protocol = "https"
    ssl_certificate_id = "arn:aws:acm:eu-west-1:523275672308:certificate/298fa9f5-4477-435b-90bf-e0b3bb7b0fb9"
  }
  health_check {
    healthy_threshold = 2
    unhealthy_threshold = 2
    timeout = 3
    target = "HTTPS:443/healthz/ready"
    interval = 30
  }
  connection_draining = true
  instances = [
    "${aws_instance.master_instance.*.id}"]
  security_groups = [
    "${aws_security_group.allow_restricted_http_and_https_elb.id}"]
  subnets = ["${aws_subnet.subnetA.id}"]
}

resource "aws_elb" "node_infra_elb" {
  name = "node-infra-elb"
  listener {
    instance_port = 80
    instance_protocol = "http"
    lb_port = 80
    lb_protocol = "http"
  }
  listener {
    instance_port = 443
    instance_protocol = "https"
    lb_port = 443
    lb_protocol = "https"
    ssl_certificate_id = "arn:aws:acm:eu-west-1:523275672308:certificate/1f4ce718-c857-452a-afa0-67aecd244cd5"
  }
  health_check {
    healthy_threshold = 2
    unhealthy_threshold = 2
    timeout = 3
    target = "TCP:443"
    interval = 30
  }
  connection_draining = true
  instances = [
    "${aws_instance.node_infra_instance.*.id}"]
  security_groups = [
    "${aws_security_group.allow_restricted_http_and_https_elb.id}"]
  subnets = ["${aws_subnet.subnetA.id}"]
}

resource "aws_elb" "gitlab_elb" {
  name = "gitlab-elb"
  listener {
    instance_port = 8081
    instance_protocol = "http"
    lb_port = 443
    lb_protocol = "https"
    ssl_certificate_id = "arn:aws:acm:eu-west-1:523275672308:certificate/298fa9f5-4477-435b-90bf-e0b3bb7b0fb9"
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
    "${aws_instance.gitlab_instance.*.id}"]
  security_groups = [
    "${aws_security_group.allow_restricted_http_and_https_elb.id}"]
  subnets = ["${aws_subnet.subnetA.id}"]
}

resource "aws_app_cookie_stickiness_policy" "master_elb_sticky" {
		name = "master-elb-sticky-policy"
		load_balancer = "${aws_elb.master_elb.id}"
		lb_port = 443
		cookie_name = "ssn"
}

resource "aws_lb_cookie_stickiness_policy" "node_infra_elb_sticky" {
		name = "node-infra-elb-sticky-policy"
		load_balancer = "${aws_elb.node_infra_elb.id}"
		lb_port = 443
		cookie_expiration_period = 600
}

resource "aws_lb_cookie_stickiness_policy" "gitlab_elb_sticky" {
		name = "gitlab-elb-sticky-policy"
		load_balancer = "${aws_elb.gitlab_elb.id}"
		lb_port = 443
		cookie_expiration_period = 600
}

resource "aws_route53_zone" "local_route53_zone" {
  name = "temenos.local"
  vpc_id = "${aws_vpc.vpc.id}"
}

resource "aws_route53_record" "external_router_route53_zone" {
  zone_id = "Z1DHMGOFTZGBIQ"
  name = "*.apps.cluster1.temenos.cloud"
  type = "CNAME"
  ttl = "30"
  records = ["${aws_elb.node_infra_elb.dns_name}"]
}

resource "aws_route53_record" "external_master_route53_zone" {
  zone_id = "Z1DHMGOFTZGBIQ"
  name = "cluster1.temenos.cloud"
  type = "CNAME"
  ttl = "30"
  records = ["${aws_elb.master_elb.dns_name}"]
}

resource "aws_route53_record" "external_gitlab_route53_zone" {
  zone_id = "Z1DHMGOFTZGBIQ"
  name = "gitlab.temenos.cloud"
  type = "CNAME"
  ttl = "30"
  records = ["${aws_elb.gitlab_elb.dns_name}"]
}
