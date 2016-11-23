variable "name"           { }
variable "environment"    { }
variable "owner"          { }
variable "stack"          { }
variable "purpose"        { }
variable "region"         { }
variable "rg_name"        { }

variable "protocol"       { default = "Tcp" }
variable "frontend_port"  { }
variable "backend_port"   { }
variable "lb_id"          { }
variable "lb_probe_id"    { }

resource "azurerm_lb_rule" "private_rule" {
  name                = "${var.environment}-${var.name}-${var.stack}-lb-rule"
  location            = "${var.region}"
  resource_group_name = "${var.rg_name}"
  loadbalancer_id     = "${var.lb_id}"              
  probe_id            = "${var.lb_probe_id}"
  protocol            = "${var.protocol}"
  frontend_port       = "${var.frontend_port}"
  backend_port        = "${var.backend_port}"
  frontend_ip_configuration_name = "${var.environment}-${var.name}-${var.stack}-${var.purpose}-lb-front_ip"
}
