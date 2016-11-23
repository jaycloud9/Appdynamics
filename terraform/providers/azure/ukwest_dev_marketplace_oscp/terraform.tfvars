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

#marketplace-deployer-tf
#client_secret   = "WOFWbluLFEMYSA/rw4vfurpyu9Qe2Q8O70bthqC6imM="
#client_secret   = "rBoP/MrJh4oYGZwJGR99xpSnctwnHM1bIyMOwQoSAqI="
sub_id			    = "d582bdcb-da11-4152-a0e9-a740933efbcf"
#tenant_id	      = "d5d2540f-f60a-45ad-86a9-e2e792ee6669"
#client_id 	    = "327b2f12-1a44-4f76-8146-049adaaef33f"

#mp-tf-demo - old portal
client_secret   = "K7xgFc7vVU+R8ITBHI3DtHmhLR81iTgktomkl5EEen8="
tenant_id	      = "d5d2540f-f60a-45ad-86a9-e2e792ee6669"
client_id 	    = "deecf6bf-315b-447a-b5fb-cd6bb6794c53"

name            = "marketplace" 
environment     = "dev"
stack           = "oscp"
owner           = "Astillion"
region          = "ukwest"

cidr            = "10.10.0.0/16"
dns_servers     = "8.8.8.8,4.4.4.4"
subnet          = "10.10.1.0/24"

tf_user         = "tfadmin"
tf_user_password= "HS7fdysnbjshbd!ndkF"
public_key      = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDYgAsBhjeEM2KTkUTwQjFer2uRyBQ6qWdkC46eJt40c2YEmEer32vylVNGvaMo9/OiObxXi0PjkzEdP8vonyJiP01Xq1yZguKPRoOhrUtXWzW45NLjZqyjiJMp8MaweIs5TA19oAQL6knWCzVQjN8tiaDlqhSmkLK1l2G3gW8iVGrWt4cUz2SJJkEKp3gN3zjGlohP5J6F6qiS+ES+TXtbW7g97rfWuMxN1m+2go96GBsR+zrsAk0Wp2U/JBCghUi2vYNEZk9dmpX/C5JVzLiIOOi44mIkgxeZvzkPeo4Qo4A76ZJeC0RZwhKGWnip6UwqReDOMDYcMxba5OF2WUGR"
