variable "name"           { }
variable "environment"    { }
variable "owner"          { }
variable "stack"          { }
variable "purpose"        { }
variable "region"         { }
variable "rg_name"        { }

variable "protocol"       { default = "Tcp" }
variable "probe"          { default = "Tcp" }
variable "backend_port"   { }
variable "lb_id"          { }




resource "azurerm_lb_probe" "tcp_lb_probe" {
  name                = "${var.environment}-${var.name}-${var.stack}-${var.purpose}-lb-probe-${var.probe}_${var.backend_port}"
  location            = "${var.region}"
  resource_group_name = "${var.rg_name}"
  loadbalancer_id     = "${var.lb_id}"
  port                = "${var.backend_port}"
  protocol            = "${var.probe}"
}

output "id" {value = "${azurerm_lb_probe.tcp_lb_probe.id}"}
