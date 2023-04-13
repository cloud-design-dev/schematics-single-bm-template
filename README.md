# Rolling IaaS Deployments Base Code

---

Rolling IaaS code as a single template split up by resource.

## Containers

The `containers/` directory houses the code for:

 - main-job = Main python app that uses the schematics SDK to run plan, apply, destroy operations on bare metal servers. 
 - clean-up = Handles the updating of OpenCancellation tickets to ensure instances are reclaimed immediately

## Terraform

Base TF code for bare metal deployments. Each Schematics workspace uses this base template. The `os` variable set for each workspace determines the OS, Datacenter, and VLANs to target
