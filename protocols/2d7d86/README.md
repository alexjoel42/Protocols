# UTI Batch qPCR Setup

### Author
[Opentrons](https://opentrons.com/)


## Categories
* PCR
	* qpcr setup

## Description
This protocols preps a 384 plate for qPCR processing. 1-14 samples can be selected. If running less than 14 samples, the protocol will pick up the correct number of tips (less than 8) to dispense across all columns in the 384 well plate. Tips are exchanged per source column in the 96 well plate.

Explanation of complex parameters below:
* `Number of Samples (1-14)`: Specify the number of samples for this run. Note: for sample numbers less than 14, place samples in order down the column beginning from column 1, with positive and negative controls always in A1 and A2, respectively. For example, patient sample 4 should be in E1, patient sample 7 should be in H1, and patient sample 8 should be in B2. If running 8 samples, the multi-channel pipette will only pick up two tips when accessing column 2 of the source plate.
* `P20 Multi-Channel Pipette Mount`: Specify which mount (left or right) to host the P20 Multi-Channel pipette.


---

### Labware
* [Opentrons 20ul Filter tips](https://shop.opentrons.com/opentrons-20ul-filter-tips/)
* Thermofisher 96 well plate
* Thermofisher 384 well plate

### Pipettes
* [P20 Multi-Channel Pipette](https://shop.opentrons.com/8-channel-electronic-pipette/)

---

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/2d7d86/Screen+Shot+2022-06-06+at+10.49.14+AM.png)

---

### Protocol Steps
1. Pipette picks up number of tips with multi-channel pipette in accordance with number of samples from source column in source plate.
2. Pipette transfers 10ul from source plate to all columns in destination plate according to plate map.
3. Pipette drops tips and proceeds to next source column if needed.

### Process
1. Input your protocol parameters above.
2. Download your protocol and unzip if needed.
3. Upload your custom labware to the [OT App](https://opentrons.com/ot-app) by navigating to `More` > `Custom Labware` > `Add Labware`, and selecting your labware files (.json extensions) if needed.
4. Upload your protocol file (.py extension) to the [OT App](https://opentrons.com/ot-app) in the `Protocol` tab.
5. Set up your deck according to the deck map.
6. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
7. Hit 'Run'.

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
2d7d86