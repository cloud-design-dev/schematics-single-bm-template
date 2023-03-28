.ONESHELL:
SHELL := /bin/zsh
.SHELLFLAGS += -e
MAKEFLAGS += --warn-undefined-variables
include .env
# export $(shell sed 's/=.*//' $(ENV_FILE))

ce-reset: ce-jr-delete ce-br-delete

push-and-follow: gh-push ce-build-run ce-submit-job

auth-target:
	ibmcloud login -a https://cloud.ibm.com -r us-south -g CDE -q
	ibmcloud ce project target --name ${PROJECT_NAME}

gh-push:
	git add . && git commit -m "Building new container image" && git push

ce-build-run:

	echo "Building container image from source..."
	
	ibmcloud ce buildrun submit --name ${BUILD_NAME}-run-$$(date +%Y%m%d%H%M) --build ${BUILD_NAME}
	
ce-submit-job:

	echo "Submitting job run to Code Engine"
	
	ibmcloud ce jobrun submit --name jobrun-$$(date +%Y%m%d%H%M)  --job ${JOB_NAME} 

	echo "run : ibmcloud ce jobrun logs -n $$(ibmcloud ce jobrun list -s age --job ${JOB_NAME} --output json | jq -r '.items[0].metadata.name') to track progress." 

ce-jr-delete:

	echo "Deleting all jobruns for ${JOB_NAME}"
	
	ibmcloud ce jobrun delete --job ${JOB_NAME} --ignore-not-found --force

ce-br-delete:
	
	echo "Deleting all buildruns for ${BUILD_NAME}"
	
	ibmcloud ce buildrun delete --build ${BUILD_NAME} --ignore-not-found --force
