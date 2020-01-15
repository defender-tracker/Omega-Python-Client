from datetime import datetime
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTShadowClient
import json
import logging

logging.basicConfig(filename='mqtt_publish.log', filemode='w', format='push_to_aws.py - %(levelname)s - %(message)s', level=logging.INFO)

def customCallback(message, something, meh):
    json_object = json.loads(message)
    formatted_message = json.dumps(json_object, indent=2)
    logging.info(formatted_message)
    logging.info(something)
    logging.info(meh)

thingName = "Tracker"

logging.info('Creating and configuring MQTT client')
myShadowClient = AWSIoTMQTTShadowClient("myClientID", useWebsocket=True)
myShadowClient.configureEndpoint("a38xjr7aj925yc-ats.iot.eu-west-1.amazonaws.com", 443)
myShadowClient.configureCredentials("root-CA.crt")
myShadowClient.configureConnectDisconnectTimeout(120)
myShadowClient.configureMQTTOperationTimeout(5)

logging.info('Creating JSON Payload')
myJSONPayload = {
    "state": {
        "reported": {
            "message": datetime.now().isoformat(),
            "Ben": "is a mahoooosive nerd"
        }
    }
}

logging.info('Connecting to AWS IoT')
myShadowClient.connect()

logging.info('Creating handler')
myDeviceShadow = myShadowClient.createShadowHandlerWithName(thingName, True)

logging.info('Updating device shadow')
myDeviceShadow.shadowUpdate(json.dumps(myJSONPayload), customCallback, 5)

