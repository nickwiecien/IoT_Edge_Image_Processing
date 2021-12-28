# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import time
import os
import requests
import cv2
import json
import asyncio

from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
from azure.iot.device.aio import IoTHubModuleClient
from azure.iot.device import Message

async def main():

    # Connect to IoT Hub
    module_client = IoTHubModuleClient.create_from_edge_environment()
    connection_established = False
    while not connection_established:
        try:
            await module_client.connect()
            connection_established = True
        except Exception as e:
            await asyncio.sleep(1)
    print("Connected IoT Hub Module Client")

    # Retrieve environment variables for upload directory, model endpoint, and relevant blob on edge attrs
    local_dir = os.environ['IMAGE_DIR']
    model_endpoint = os.environ['MODEL_ENDPOINT']

    blob_connstr = os.environ['LOCAL_BLOB_CONN_STR']
    raw_container = os.environ['RAW_CONTAINER']
    annotated_container = os.environ['ANNOTATED_CONTAINER']

    # Connect to blob on edge and verify that target containers exist
    blob_service_client = BlobServiceClient.from_connection_string(blob_connstr, api_version='2019-07-07')
    try:
        raw_container_client = blob_service_client.create_container(raw_container)
    except Exception as e:
        pass
    try:
        annotated_container_client = blob_service_client.create_container(annotated_container)
    except Exception as e:
        pass

    # Create clients for raw/annotated image containers 
    raw_container_client = blob_service_client.get_container_client(raw_container)
    annotated_container_client = blob_service_client.get_container_client(annotated_container)

    # Continuously monitor local directory where images are uploaded
    while True:
        files = os.listdir(local_dir)
        for file in files:
            # Load image and send to scoring endpoint
            full_path = os.path.join(local_dir, file)
            frame = cv2.imread(full_path)
            annotated_frame = frame
            encoded_frame = cv2.imencode(".jpg", frame)[1].tobytes()
            headers = {"Content-Type": "application/octet-stream"}
            response = requests.post(model_endpoint, headers=headers, data=encoded_frame)
            result = response.json()

            # If predictions are found add annotations to raw image based on bounding box coordinates
            if len(result)>0:
                if "predictions" in result:
                    for pred in result['predictions']:
                        probability = pred["probability"]
                        bbox = pred["boundingBox"]
                        tag_name = pred["tagName"]
                        tagId = pred["tagId"]
                        height, width, channel = frame.shape
                        xmin = int(bbox["left"] * width)
                        xmax = int((bbox["left"] * width) + (bbox["width"] * width))
                        ymin = int(bbox["top"] * height)
                        ymax = int((bbox["top"] * height) + (bbox["height"] * height))
                        start_point = (xmin, ymin)
                        end_point = (xmax, ymax)
                        color = (0, 255, 0)
                        thickness = 3
                        annotated_frame = cv2.rectangle(annotated_frame, start_point, end_point, color, thickness)
                        annotated_frame = cv2.putText(annotated_frame, tag_name, start_point, fontFace = cv2.FONT_HERSHEY_COMPLEX, fontScale = 0.5, color = (0,0, 255))

                    # Save raw/annotated images to blob on edge
                    # Note: with auto-tiering configured these images will be moved to an Azure Blob Storage account
                    # automatically.
                    raw_name = file.split('.')[0] + '.jpg'
                    annotated_name = raw_name.replace('.jpg', '_annotated.jpg')
                    annotated_frame = cv2.imencode(".jpg", annotated_frame)[1].tobytes()

                    raw_container_client.upload_blob(name = raw_name, data = encoded_frame)
                    annotated_container_client.upload_blob(name=annotated_name, data=annotated_frame)

                    # Send message to IoT Hub with location of raw & annotated images
                    json_data = {'raw_image_location': '{}/{}'.format(raw_container, raw_name),
                    'annotated_image_location': '{}/{}'.format(annotated_container, annotated_name)}
                    message = Message(bytearray(json.dumps(json_data), "utf8"))
                    await module_client.send_message_to_output(message, "Events")
                    print(json_data)

                    # Remove image from upload dir
                    os.remove(full_path)

        # Sleep 1 second then check directory again
        time.sleep(1)


if __name__ == "__main__":
    #main()
    asyncio.run(main())
