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

#--------------------------------------------------------------
# Global
#--------------------------------------------------------------


domain              = "temenos.cloud"
ssl_certificate_id  = "arn:aws:acm:eu-west-1:523275672308:certificate/298fa9f5-4477-435b-90bf-e0b3bb7b0fb9"
name                = "global"
region              = "eu-west-1"


#--------------------------------------------------------------
# Env
#--------------------------------------------------------------

name              = "dev"
ami               = "ami-8b8c57f8"
region            = "eu-west-1"
key_pair_name     = "key_pair"
# Below does not work but text version of key does
#key_public_key    = "${file("../../../../keys/key.pub")}"

#--------------------------------------------------------------
# Network
#--------------------------------------------------------------

vpc_cidr        = "10.0.0.0/16"
azs             = "eu-west-1a,eu-west-1b,eu-west-1c" # AZs are region specific
public_subnets  = "10.0.1.0/24,10.0.2.0/24,10.0.3.0/24" # Creating one public subnet per AZ

#--------------------------------------------------------------
# Compute
#--------------------------------------------------------------
