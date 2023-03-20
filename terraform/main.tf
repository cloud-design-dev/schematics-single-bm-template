locals {
  date   = formatdate("MM-DD", timestamp())
  prefix = "${var.deployment["${var.os}"]["name"]}-${local.date}"

  tags = [
    "project:rolling-iaas",
    "owner:ryantiffany",
    "datacenter:${var.deployment["${var.os}"]["datacenter"]}",
  ]
}

resource "ibm_compute_bare_metal" "rolling" {
  package_key_name       = var.package_key_name
  process_key_name       = var.process_key_name
  memory                 = 192
  os_key_name            = var.deployment["${var.os}"]["os_reference_code"]
  hostname               = local.prefix
  domain                 = var.domain
  datacenter             = var.deployment["${var.os}"]["datacenter"]
  network_speed          = var.network_speed
  public_bandwidth       = 20000
  disk_key_names         = ["HARD_DRIVE_1_00_TB_SATA_2", "HARD_DRIVE_1_00_TB_SATA_2"]
  hourly_billing         = false
  private_network_only   = false
  unbonded_network       = true
  public_vlan_id         = var.deployment["${var.os}"]["public_vlan_number"]
  private_vlan_id        = var.deployment["${var.os}"]["private_vlan_number"]
  tags                   = local.tags
  redundant_power_supply = true
  user_metadata          = var.deployment["${var.os}"]["user_metadata"]

  storage_groups {
    # RAID 1
    array_type_id = 2
    # Use the first two disks
    hard_drives = [0, 1]
    array_size  = 1000

  }
}

#   user_metadata = templatefile("${path.module}/centos.tftpl", {
#     logdna_ingestion_key     = "${data.ibm_secrets_manager_secret.logdna_ingestion_key.secret_data.payload}",
#     monitoring_ingestion_key = "${data.ibm_secrets_manager_secret.monitoring_ingestion_key.secret_data.payload}",
#     region                   = "us-south"
#   })