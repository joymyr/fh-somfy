# Somfy integration for Futurehome

This integration is using [python-overkiz-api](https://github.com/iMicknl/python-overkiz-api) 
to integrate Somfy with futurehome.
Supported devices will be automatically added to FH when running this integration.
Currently supported devices is screens and light sensors.

## Requirements

* Somfy Connexoon IO (other hubs supported by python-overkiz-api might also work)
* Futurehome hub
* A local device where you can run this Pyhon code, i.e. a Raspberry PI

## Setup

* First enable local api in the Futurehome hub settings
* Then install this project on a local device:
```bash
pip install pyoverkiz
pip install paho-mqtt
git clone <this repo>
```

## Configuration

Edit const.py and set the required parameters

```
SOMFY_USERNAME = "<Somfy app username>"
SOMFY_PASSWORD = "<Somfy app password>"
MQ_ADDRESS = "<Ip address of your Futurehome hub>"
MQ_USERNAME = "<Futurehome mq username>"
MQ_PASSWORD = "<Futurehome mq password>"
```

## Run

Run the code

```
python main.py
```
