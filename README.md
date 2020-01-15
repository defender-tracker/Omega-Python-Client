# Defender Tracker - Omega Python Client

## Introduction
This is the repository that will contain the code that:
 - recieves NMEA dumps from the on-board GNSS chip
 - understands it and converts it into a useful format
 - saves the full message to the on-board SD card
 - publishes a sub-set of the data to AWS over MQTT using the cellular connection

All upstream processes will be defined and built in a different repository.

## Getting it running
You should only need to clone this repository and then run:
```pip install -r requirements.txt```

followed by:
```python push_to_aws.py```

## Branching
If you want to add capability to this file, create a branch and then raise a pull request to merge changes into the master branch.