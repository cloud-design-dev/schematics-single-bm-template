locals {
  date   = formatdate("MM-DD-YY", timestamp())
  prefix = "cde-${local.date}-${var.deployment["${var.os}"]["name"]}"

  tags = [
    "project:rolling-iaas",
    "owner:ryantiffany",
    "datacenter:${var.deployment["${var.os}"]["datacenter"]}",
  ]
}

resource "ibm_compute_vm_instance" "rolling" {
  hostname                 = local.prefix
  domain                   = var.domain
  os_reference_code        = var.deployment["${var.os}"]["os_reference_code"]
  datacenter               = var.deployment["${var.os}"]["datacenter"]
  network_speed            = 1000
  hourly_billing           = true
  local_disk               = true
  private_network_only     = false
  flavor_key_name          = "BL2_2X8X100"
  tags                     = local.tags
  public_vlan_id           = var.deployment["${var.os}"]["public_vlan_number"]
  private_vlan_id          = var.deployment["${var.os}"]["private_vlan_number"]
  dedicated_acct_host_only = false
  ipv6_enabled             = true
  user_metadata            = var.deployment["${var.os}"]["user_metadata"]
}