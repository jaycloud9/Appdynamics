variable "name"                   { }
variable "environment"            { }
variable "owner"                  { }
variable "stack"                  { }
variable "region"                 { }
variable "rg_name"                { }

variable "network_inf"            { }
variable "vm_size"                { }
variable "os_storage_container"   { }
variable "tf_admin_passwd"        { }
variable "tf_user"                { }
variable "public_key"             { }
variable "type"                   { }


resource "azurerm_virtual_machine" "rhel_7" {
  name                  = "${var.environment}-${var.name}-${var.stack}-${var.type}-vm"
  location              = "${var.region}"
  resource_group_name   = "${var.rg_name}"

  network_interface_ids = ["${var.network_inf}"]
  vm_size               = "${var.vm_size}"


  storage_image_reference {
    publisher = "RedHat"
    offer     = "RHEL"
    sku       = "7.3"
    version   = "latest"
  }

  storage_os_disk {
    name          = "${var.environment}-${var.name}-${var.stack}-vm_disk"
    vhd_uri       = "${var.os_storage_container}/${var.environment}-${var.name}-${var.stack}-${var.type}-os.vhd"
    caching       = "ReadWrite"
    create_option = "FromImage"
  }
  
	storage_data_disk {
    name          = "datadisk0"
    vhd_uri       = "${var.os_storage_container}/${var.environment}-${var.name}-${var.stack}-${var.type}-data.vhd"
    disk_size_gb  = "500"
    create_option = "empty"
    lun           = 0
  }

  os_profile {
    computer_name   = "${var.environment}-${var.name}"
    admin_username  = "${var.tf_user}"
    admin_password  = "${var.tf_admin_passwd}"
  }
  os_profile_linux_config {
    disable_password_authentication = false
    ssh_keys {
      path = "/home/${var.tf_user}/.ssh/authorized_keys"
      key_data = "${var.public_key}"
    }
  }

  tags {
    Environment = "${var.environment}"
    Stack       = "${var.stack}"
    Owner       = "${var.owner}"
    Type        = "${var.type}"
  }
}
