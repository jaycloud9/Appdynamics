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

#client_secret   = "WOFWbluLFEMYSA/rw4vfurpyu9Qe2Q8O70bthqC6imM="
client_secret   = "rBoP/MrJh4oYGZwJGR99xpSnctwnHM1bIyMOwQoSAqI="
sub_id			    = "d582bdcb-da11-4152-a0e9-a740933efbcf"
tenant_id	      = "d5d2540f-f60a-45ad-86a9-e2e792ee6669"
client_id 	    = "327b2f12-1a44-4f76-8146-049adaaef33f"

name            = "marketplace" 
environment     = "dev"
stack           = "oscp"
owner           = "Astillion"

