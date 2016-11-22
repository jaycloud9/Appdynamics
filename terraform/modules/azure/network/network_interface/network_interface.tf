variable "name"               { }
variable "environment"        { }
variable "stack"              { }
variable "owner"              { }
variable "subnet_id"          { }
variable "rg_name"            { }
variable "region"             { }
variable "lb_backend_pool_id" { }

resource "azurerm_public_ip" "public" {
  name  = "${var.environment}-${var.name}-${var.stack}-pub-ip"
  location  = "${var.region}"
  resource_group_name = "${var.rg_name}"
  public_ip_address_allocation = "static"
    
  tags {
    Environment = "${var.environment}"
    Stack       = "${var.stack}"
    Owner       = "${var.owner}"
  }
}

resource "azurerm_network_interface" "NIC" {
  name  = "${var.environment}-${var.name}-${var.stack}-vnet"
  location  = "${var.region}"
  resource_group_name = "${var.rg_name}"

  ip_configuration {
    name = "${var.environment}-${var.name}-${var.stack}-ipconf"
    subnet_id = "${var.subnet_id}"
    private_ip_address_allocation = "Dynamic"
		public_ip_address_id = "${azurerm_public_ip.public.id}"
    load_balancer_backend_address_pools_ids = ["${var.lb_backend_pool_id}"]
  }
  tags {
    Environment = "${var.environment}"
    Stack       = "${var.stack}"
    Owner       = "${var.owner}"
  }
}

output "id" { value = "${azurerm_network_interface.NIC.id}" }
