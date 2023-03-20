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
      os_reference_code   = "OS_WINDOWS_2022_FULL_STD_64_BIT"
      name                = "win"
      datacenter          = "dal10"
      public_vlan_number  = 2998166
      private_vlan_number = 2998168
      user_metadata       = null
    },
    centos = {
      os_reference_code   = "OS_CENTOS_STREAM_8_X_64_BIT"
      name                = "centos"
      datacenter          = "wdc06"
      public_vlan_number  = 3313878
      private_vlan_number = 3313880
      user_metadata       = "user-data/centos.yml"
    },
    ubuntu = {
      os_reference_code   = "OS_UBUNTU_22_04_LTS_JAMMY_JELLYFISH_64_BIT"
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

variable "package_key_name" {
  description = "BM Package keyname to use."
  type        = string
  default     = "DUAL_INTEL_XEON_PROCESSOR_SCALABLE_FAMILY_4_DRIVES"
}

variable "domain" {
  description = "Domain for deployed server."
  type        = string
  default     = "gh40.net"
}

variable "process_key_name" {
  description = "BM Process keyname to use."
  type        = string
  default     = "INTEL_INTEL_XEON_5120_2_20"
}

variable "network_speed" {
  description = "Default Network speed for BM hosts."
  type        = number
  default     = 10000
}