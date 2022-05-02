# Home Network Overlord - DNS Admin

The webserver that wraps pihole to allow one-touch "blacklist" of domains via mqttthing/ homekit on iOS

### Requires:
 - [Homebridge: MQTT Thing](https://github.com/arachnetech/homebridge-mqttthing)
 - [NodeRed](https://nodered.org/)
 - [Gunicorn/ Flask ](https://gunicorn.org/)
 - [Pihole ](https://pi-hole.net/)

### Other Notes

 1. Once the new pihole api is released, will potentially be deprecated
 1. Design choice: keep node-red focused on transport than the heavy lifting of config management
 1. Design limitation:
