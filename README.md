# Rolling IaaS Deployments Base Code

---

Rolling IaaS code as a single template split up by resource.

```
├── containers/
│   ├── main-job: Main python app that uses the schematics SDK to run plan, apply, destroy operations on bare metal servers
│   └── clean-up: Handles the updating of OpenCancellation tickets to ensure instances are reclaimed immediately 
└── terraform: Base TF code for bare metal deployments. Each Schematics workspace uses this base template
```

## Todo
 - Update code engine builds to use new url for base code 
 - add updates to all subfolder readmes

