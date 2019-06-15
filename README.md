# Home-Assistant stuff

This is my repository of home-assistant related stuff. 



# Unifi Sensor

This sensor
shows the number of devices connected to your unifi APs and also shows the devices per AP and per ESSID as attributes
of the sensor.

![unifi sensor](https://github.com/clyra/homeassistant/blob/master/unifi_sensor.png?raw=true)

## Install

Copy my_unifi folder to your home-assistant custom_components folder.

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

Copy climatempo folder to your home-assistant custom_components folder.

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
# Humanity

A custom component that fetch today and tomorrow shifts from humanity.com.

## Install

Copy humanity folder to your home-assistant custom_components folder.

## configure

You will have to ask for api access on humanity website. Then got to settings -> Integration API v2 and create a API Application there. There's no need of a "Redirection URI". You will need to copy App ID and App Secret from this page. If this info, configure the component on HA:      

```yaml
sensor:
   - platform: humanity
     name: <whatever you want> (optional, default "climatempo")
     app_id: <your app_id>
     app_secret: <your app_secret>
     username: <username used to login on humanity>
     password: <password used to login on humanity>
```

Create a entities card on lovelace to show the today and tomorrow sensors.
