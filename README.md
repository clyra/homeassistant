# Home-Assistant stuff

This is my repository of home-assistant related stuff. For now, check the unifi sensor :-). This sensor
shows the number of devices connected to your unifi APs and also shows the devices per AP and per ESSID as attributes
of the sensor.

![unifi sensor](https://github.com/clyra/homeassistant/blob/master/unifi_sensor.png?raw=true)

## Install

Copy sensor/unifi.py to your home-assistant custom_components/sensor folder.

## Configure

Add the following to your sensors configuration:

```yaml
sensor:
   - platform: unifi
     name: <whatever you want> (optional, default: "unifi")
     region: <site name> (optional, default: "default")
     username: <unifi_controller_username>
     password: <unifi_controller_password>
     url: https://x.x.x.x:8443 <or your unifi controller url>
```


