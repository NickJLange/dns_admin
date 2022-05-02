# Home Network Overlord - DNS Admin

The webserver that wraps pihole to allow one-touch "blacklist" of domains via mqttthing/ homekit on iOS - so that you don't need to do all or nothing.

### Requires:
 - [Homebridge: MQTT Thing](https://github.com/arachnetech/homebridge-mqttthing)
 - [NodeRed](https://nodered.org/)
 - [Gunicorn/ Flask ](https://gunicorn.org/)
 - [Pihole ](https://pi-hole.net/)

### Disclaimers

 1. Once the new pihole api is released, will potentially be deprecated
 1. Design choice: keep node-red focused on transport than the heavy lifting of config management
 1. Design limitation: MQTT Thing doesn't support dynamic accessories currently, so each provider will need


### See Also:
 - [Homebridge - Pihole ](https://github.com/arendruni/homebridge-pihole#readme)

### NodeRed Config

- See folder node_red_flows for an example parser

### Homebridge MQTT Thing Config Example

 ```

 {
     "type": "switch",
     "name": "${provider_friendly}",
     "url": "${mqtt_address}",
     "mqttOptions": {
         "keepalive": 30
     },
     "logMqtt": false,
     "debounceRecvms": 100,
     "optimizePublishing": false,
     "topics": {
         "getOn": "dns_controller/media/${provider}/status",
         "setOn": "dns_controller/media/${provider}/change"
     },
     "onValue": "on",
     "offValue": "off",
     "accessory": "mqttthing"
 },

 ```
