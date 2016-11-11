#--------------------------------------------------------------
# General
#--------------------------------------------------------------

# When using the GitHub integration, variables are not updated
# when checked into the repository, only when you update them
# via the web interface. When making variable changes, you should
# still check them into GitHub, but don't forget to update them
# in the web UI of the appropriate environment as well.

# If you change the atlas_environment name, be sure this name
# change is reflected when doing `terraform remote config` and
# `terraform push` commands - changing this WILL affect your
# terraform.tfstate file, so use caution

name              = "dev"
region            = "eu-west-1"
key_pair_name     = "key_pair"
key_public_key    = "${file("../../../keys/key.pub")}"

#--------------------------------------------------------------
# Network
#--------------------------------------------------------------

vpc_cidr        = "10.0.0.0/16"
azs             = "eu-west-1a,eu-west-1b,eu-west-1c" # AZs are region specific
public_subnets  = "10.0.1.0/24,10.0.2.0/24,10.0.3.0/24" # Creating one public subnet per AZ

#--------------------------------------------------------------
# Compute
#--------------------------------------------------------------
