# binary_sensor.flexget
Binary Sensor for [Flexget](https://www.flexget.com) to get information on tasks run.

I stole this script from [Tommatheussen](https://github.com/Tommatheussen/Home-Assistant-Configuration/tree/master/custom_components/binary_sensor).

It stopped working so I somehow hacked it together and it works again. For me. Sort of? You have been warned.

Hopefully someone else who knows what they are doing can take this on again.

More info can be found [here](https://community.home-assistant.io/t/flexget-integration/11302)

The sensor will be in an ON state when a task succeeds with its attributes filled with a bunch of info.

## Installation
1. Install the component by copying it into your `/custom_components/flexget/` folder.
2. Add the code to your `configuration.yaml` using the variables below.

**Example config**
```yaml
binary_sensor:
    platform: flexget
    username: flexget
    password: password
    host: 127.0.0.1
    port: 5050
    check_version: false
    tasks:
        - my-flexget-task
```

**Configuration variables:**

key | type | description
:--- | :--- | :---
**platform (Required)** | string | `flexget`
**password (Required)** | string | Password for flexget webui
**username (Optional)** | string | Username (Default: flexget)
**host (Optional)** | string | Host address of Flexget (Default: 127.0.0.1)
**port (Optional)** | number | Port for flexget. (Default: 5050)
**check_version (Optional)** | boolean | Create a sensor to check if a new flexget version is available. (Default: True)
**tasks (Optional)** | array | List of tasks you want to track. Otherwise will get all.

***

## Version History
Version | Description
:--- | :---
0.0.2 | Initial fix release for HA 0.92
0.0.3 | More fixes. Added version update checker.