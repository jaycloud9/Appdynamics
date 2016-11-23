variable "name"           { }
variable "environment"    { }
variable "owner"          { }
variable "stack"          { }
variable "purpose"        { }
variable "region"         { }
variable "rg_name"        { }

variable "protocol"       { default = "Tcp" }
variable "subnet_id"      { }
variable "frontend_port"  { }
variable "backend_port"   { }


resource "azurerm_public_ip" "public_ip" {
  name  = "${var.environment}-${var.name}-${var.stack}-${var.purpose}lb-pub-ip"
  location  = "${var.region}"
  resource_group_name = "${var.rg_name}"
  public_ip_address_allocation = "static"

  tags {
    Environment = "${var.environment}"
    Stack       = "${var.stack}"
    Owner       = "${var.owner}"
  }
}

resource "azurerm_lb" "public_lb" {
  name                = "${var.environment}-${var.name}-${var.stack}-${var.purpose}-lb"  
  location            = "${var.region}"
  resource_group_name = "${var.rg_name}"

  frontend_ip_configuration {
    name      = "${var.environment}-${var.name}-${var.stack}-${var.purpose}-lb-front_ip"
		public_ip_address_id = "${azurerm_public_ip.public_ip.id}"
  }
  tags {
    Environment = "${var.environment}"
    Stack       = "${var.stack}"
    Owner       = "${var.owner}"
  }
}

resource "azurerm_lb_backend_address_pool" "public_lb_backend" {
  name                = "${var.environment}-${var.name}-${var.stack}-${var.purpose}-lb-front_ip"  
  location            = "${var.region}"
  resource_group_name = "${var.rg_name}"
  loadbalancer_id     = "${azurerm_lb.public_lb.id}"  
}

output "lb_name"  { value = "${azurerm_lb.public_lb.name}" }
output "lb_id"    { value = "${azurerm_lb.public_lb.id}" }

output "lb_backend_pool_name"  { value = "${azurerm_lb_backend_address_pool.public_lb_backend.name}" }
output "lb_backend_pool_id"    { value = "${azurerm_lb_backend_address_pool.public_lb_backend.id}" }
