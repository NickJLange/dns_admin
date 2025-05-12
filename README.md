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

### config.ini sample
FIXME on symlink
```
[general]
remote_pi_list: $IP_OR_DNS_OF_PIHOLE, SPACE SEPARATED
#set REMOTE_PI_LIST environmental variable as well

# pihole_version < 6
remote_pi_password: $PASSWORD
remote_pi_token: $TOKEN
#set remote_pi_password(s) - also set via REMOTE_PI_PASSWORD environment variable


### env equiv REMOTE_UBIQUITI[_USERNAME|_PASSWORD]


[ubiquiti]
remote_ubiquiti_device: $UDM
remote_ubiquiti_username: $UDM_USERNAME
remote_ubiquiti_password: $UDM_PASSWORD

[ubiquiti_targets]
kids_macs: $MAC_ADDR
           $MAC_ADDR2
           $MAC_ADDR3
laptop: $MAC_ADDR4

[ubiquiti_rules]
rules:  $RULE1
        $RULE2


[domains]
dplus:  disneyplus.com
        bamgrid.com
        bam.nr-data.net
        cdn.registerdisney.go.com
        cws.conviva.com
        d9.flashtalking.com
        disney-portal.my.onetrust.com
        disneyplus.bn5x.net
        js-agent.newrelic.com
        disney-plus.net
        dssott.com
        adobedtm.com
        choosey.com

netflix: netflix.com

hbomax: hbo.com

youtube:youtube.com
        googlevideo.com
        youtu.be
        youtubei.googleapis.com
        ytimg.com
        zytimg.com

playstation: playstation.net
minecraft: minecraft.net
```
