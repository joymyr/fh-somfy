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

* Enable local api in the Futurehome hub settings
* Install Python3 on a local device
```
# Example for Debian-based systems
sudo apt-get install python3 python3-pip
```

* Install this project and required dependencies
```bash
pip3 install pyoverkiz paho-mqtt
git clone https://github.com/joymyr/fh-somfy.git
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
python3 main.py
```

## Run on boot

Use systemctl to run the code on boot.
The fh_somfy.service file is intended for a Raspberry Pi.

```
sudo cp fh_somfy.service /lib/systemd/system/
sudo chmod 644 /lib/systemd/system/fh_somfy.service
sudo systemctl daemon-reload
sudo systemctl enable fh_somfy.service
```
