variable "name"           { }
variable "environment"    { }
variable "owner"          { }
variable "stack"          { }
variable "purpose"        { }
variable "region"         { }
variable "rg_name"        { }

variable "probe"          { default = "Http" }
variable "backend_port"   { }
variable "probe_path"     { }
variable "lb_id"          { }


resource "azurerm_lb_probe" "http_lb_probe" {
  name                = "${var.environment}-${var.name}-${var.stack}-${var.purpose}-lb-probe-${var.probe}_${var.backend_port}"
  location            = "${var.region}"
  resource_group_name = "${var.rg_name}"
  loadbalancer_id     = "${var.lb_id}"
  port                = "${var.backend_port}"
  protocol            = "${var.probe}"
  request_path        = "${var.probe_path}"
}

output "id" {value = "${azurerm_lb_probe.http_lb_probe.id}"}
