variable "name"           { }
variable "environment"    { }
variable "owner"          { }
variable "stack"          { }
variable "region"         { }
variable "rg_name"        { }

variable "protocol"       { default = "Tcp" }
variable "probe"          { default = "Http" }
variable "subnet_id"      { }
variable "frontend_port"  { }
variable "backend_port"   { }
variable "probe_path"     { }

resource "azurerm_lb" "private_lb" {
  name                = "${var.environment}-${var.name}-${var.stack}-lb"  
  location            = "${var.region}"
  resource_group_name = "${var.rg_name}"

  frontend_ip_configuration {
    name      = "${var.environment}-${var.name}-${var.stack}-lb-front_ip"  
    subnet_id = "${var.subnet_id}"
    private_ip_address_allocation = "Dynamic"
  }
  tags {
    Environment = "${var.environment}"
    Stack       = "${var.stack}"
    Owner       = "${var.owner}"
  }
}

resource "azurerm_lb_backend_address_pool" "private_lb_backend" {
  name                = "${var.environment}-${var.name}-${var.stack}-lb-front_ip"  
  location            = "${var.region}"
  resource_group_name = "${var.rg_name}"
  loadbalancer_id     = "${azurerm_lb.private_lb.id}"  
}

resource "azurerm_lb_probe" "private_lb_probe" {
  name                = "${var.environment}-${var.name}-${var.stack}-lb-probe-${var.probe}_${var.backend_port}"  
  location            = "${var.region}"
  resource_group_name = "${var.rg_name}"
  loadbalancer_id     = "${azurerm_lb.private_lb.id}"  
  port                = "${var.backend_port}"
  protocol            = "${var.probe}"
  request_path        = "${var.probe_path}"
}

resource "azurerm_lb_rule" "private_rule" {
  name                = "${var.environment}-${var.name}-${var.stack}-lb-rule"  
  location            = "${var.region}"
  resource_group_name = "${var.rg_name}"
  loadbalancer_id     = "${azurerm_lb.private_lb.id}"  
  probe_id            = "${azurerm_lb_probe.private_lb_probe.id}"
  protocol            = "${var.protocol}"
  frontend_port       = "${var.frontend_port}"
  backend_port        = "${var.backend_port}"
  frontend_ip_configuration_name = "${var.environment}-${var.name}-${var.stack}-lb-front_ip"
}

output "lb_name"  { value = "${azurerm_lb.private_lb.name}" }
output "lb_id"    { value = "${azurerm_lb.private_lb.id}" }

output "lb_backend_pool_name"  { value = "${azurerm_lb_backend_address_pool.private_lb_backend.name}" }
output "lb_backend_pool_id"    { value = "${azurerm_lb_backend_address_pool.private_lb_backend.id}" }
