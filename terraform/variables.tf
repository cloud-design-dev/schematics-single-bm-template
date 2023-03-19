variable "deployment" {
  description = "Deployment options to use based on var.os. This also determines the Datacenter and VLANs."
  type = map(object({
    os_reference_code   = string
    name                = string
    datacenter          = string
    public_vlan_number  = number
    private_vlan_number = number
    user_metadata       = string
  }))
  default = {
    windows = {
      os_reference_code   = "WIN_2022-STD_64"
      name                = "windows"
      datacenter          = "dal10"
      public_vlan_number  = 2998166
      private_vlan_number = 2998168
      user_metadata       = "user-data/windows.ps1"
    },
    centos = {
      os_reference_code   = "ROCKYLINUX_8_64"
      name                = "centos"
      datacenter          = "wdc06"
      public_vlan_number  = 3313878
      private_vlan_number = 3313880
      user_metadata       = "user-data/centos.yml"
    },
    ubuntu = {
      os_reference_code   = "UBUNTU_20_64"
      name                = "ubuntu"
      datacenter          = "lon06"
      public_vlan_number  = 3309424
      private_vlan_number = 3309426
      user_metadata       = "user-data/ubuntu.yml"
    }
  }
}

variable "os" {
  description = "Operating system to deploy."
  type        = string
}

variable "instance_profile" {
  description = "Instance profile to use."
  type        = string
  default     = "BL2_2X8X100"
}

variable "domain" {
  description = "Domain for deployed server."
  type        = string
  default     = "gh40.net"
}