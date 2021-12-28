# IoT Edge/Custom Vision Sample
Sample IoT Edge solution that demonstrates how to: 
* Run an Azure Custom Vision (object detection) model as an edge module with exposed via a RESTful endpoint
* Score incoming images (added to a target directory on the edge device) using the Custom Vision model
* Annotate scored images with bounding boxes and labels corresponding to detected objects
* Save raw/annotated images to Azure Blob Storage on Edge and auto-tier those images to an Azure Storage Account
* Send messages to IoT Hub following successful inferencing

For the purposes of this demo, the deployed model will detect face suit and color of playing cards and annotate images as is show below. Sample images are included in the `sample_images` dir.

![Annotated Image Sample](SampleImageScoring/img/IMG_2560_annotated.jpg?raw=true "Annotated Image Sample")

## Required Azure Resources
The following resources should be provisioned prior to deploying the sample edge solution:
* Azure IoT Hub
* Azure Container Registry
* Azure Storage Account
* Azure Virtual Machine running Linux (simulated edge device; recommend Standard_DS2_V3 running Ubuntu 18.04/20.04 LTS)

## Demo Setup
From your IoT Hub instance, navigate to IoT Edge along the left blade and click `+ Add IoT Edge Device`. Give your new device a unique ID and click `Save`.

Connect to your Linux VM via a new RDP session - details on logging into your VM via RDP [can be found here](https://docs.microsoft.com/en-us/azure/virtual-machines/linux/use-remote-desktop). From your VM, follow the steps outlined in [this blog post](https://pineview.io/blog/azure-iot-edge-nodejs/) to install the IoT Edge runtime and connect to IoT Hub as a new device. Finally, create a folder on the desktop named `image_drop`. This folder will be bound to the ScoreAndAnnotate container in a subsequent step and will be used to accept input images. 

Clone this repo and open inside of VS Code. For development purposes, please install the [Azure IoT Device Workbench extension](https://marketplace.visualstudio.com/items?itemName=vsciot-vscode.vscode-iot-workbench) and the [Azure IoT Edge extension](https://marketplace.visualstudio.com/items?itemName=vsciot-vscode.azure-iot-edge). First, create a new file `.env` inside the `SampleImageScoring` directory. Copy the environment variables listed in `sample.env` and update all fields with values that map to your newly provisioned Azure resources. For the `BLOB_ON_EDGE_ACCOUNT_KEY`, generate a new 64-byte Base64 string using [this tool](https://generate.plus/en/base64).

Using the Azure CLI, login to your Azure subscription as well as your Azure Container Registry using the commands below - follow all steps when prompted.
* `az login`
* `az acr login --name <YOUR_CONTAINER_REGISTRY_NAME>`

Connect to your provisioned IoT Hub. From the VS Code command pallete, search for `Azure IoT Hub: Set IoT Hub Connection String`. Add the connection string for your IoT Hub associated with the iothubowner shared access policy. You should see your created device appear in the lower left-hand window under the heading Azure IoT Hub.

Inside the `modules/CustomVisionModel` and `modules/ScoreAndAnnotate` directories, update the `module.json` files to reflect the name of your new container registry.

From the VS Code Command pallete, search for `Azure IoT Edge: Build and Push IoT Edge Module` and build and push the amd64 versions of both the `CustomVisionModel` and `ScoreAndAnnotate` modules. 

Right-click the `deployment.template.json` file and select Generate IoT Edge Deployment Manifest. Once the new deployment manifest is created - `config/deployment.amd64.json` - right-click and select Create Deployment for Single Device, and select your target device.



