# Home-Assistant stuff

This is my repository of home-assistant related stuff. 



# Unifi Sensor

This sensor
shows the number of devices connected to your unifi APs and also shows the devices per AP and per ESSID as attributes
of the sensor.

![unifi sensor](https://github.com/clyra/homeassistant/blob/master/unifi_sensor.png?raw=true)

## Install

Copy sensor/unifi.py to your home-assistant custom_components/sensor folder.

## Configure

Add the following to your sensors configuration:

```yaml
sensor:
   - platform: my_unifi
     name: <whatever you want> (optional, default: "unifi")
     region: <site name> (optional, default: "default")
     username: <unifi_controller_username>
     password: <unifi_controller_password>
     url: https://x.x.x.x:8443 <or your unifi controller url>
```

# Climatempo

A Weather component that fetch the weather condition and forecast from climatempo.com.br.

## Install

Copy climatempo.py to your home-assistant custom_components/weather folder.

## Configure

You will need a api_key to be able to use this component. Go to https://advisor.climatempo.com.br, login, Tokens and create a new projet.
Find your city code using http://apiadvisor.climatempo.com.br/api/v1/locale/city?name=yourcity&state=yourstate&token=your-app-token

Add the following to your weather configuration:

```yaml
weather:
   - platform: climatempo
     name: <whatever you want> (optional, default "climatempo")
     api_key: <your token>
     city: <city_code>
```

