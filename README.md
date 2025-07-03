# LoRaWAN - RFID Hybrid System

This project aims to simulate and analyze the payload transmission of RFID EPCs over LoRaWAN using different parameters.


 What it does :
 
- Encodes a list of EPCs (12-byte hex identifiers)
- Calculates LoRaWAN airtime and payload size
- Determines the number of packets needed
- Computes how many EPCs can be sent per day (based on duty cycle)
- Compares multiple SF settings

 How to run :

Just run the script:

```bash
python Testing.py

