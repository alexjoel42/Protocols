from opentrons import labware, instruments, robot
from otcustomizers import StringSelection, FileInput

metadata = {
    'protocolName': 'PCR Prep',
    'author': 'Opentrons <protocols@opentrons.com>',
    'source': 'Protocol Library'
    }

mastermix_csv_example = """
Reagent,Slot,Well,Volume
Buffer,1,A2,25
MgCl,1,A3,40
dNTPs,2,A2,90
Water,2,A3,248
primer 1,1,A4,25
primer 2,1,A5,25
"""


def run_custom_protocol(
        left_pipette: StringSelection(
            'p10-single', 'P50-single', 'p300-single',
            'p1000-single')='p50-single',
        right_pipette: StringSelection(
            'p10-single', 'P50-single', 'p300-single',
            'p1000-single')='p300-single',
        master_mix_csv: FileInput=mastermix_csv_example
        ):

    def mount_pipette(pipette_type, mount, tiprack_slot):
        if pipette_type == 'p10-single':
            tip_rack = labware.load('tiprack-10ul', tiprack_slot)
            pipette = instruments.P10_Single(
                mount=mount,
                tip_racks=[tip_rack])
        elif pipette_type == 'p50-single':
            tip_rack = labware.load('opentrons-tiprack-300ul', tiprack_slot)
            pipette = instruments.P50_Single(
                mount=mount,
                tip_racks=[tip_rack])
        elif pipette_type == 'p300-single':
            tip_rack = labware.load('opentrons-tiprack-300ul', tiprack_slot)
            pipette = instruments.P300_Single(
                mount=mount,
                tip_racks=[tip_rack])
        else:
            tip_rack = labware.load('tiprack-1000ul', tiprack_slot)
            pipette = instruments.P1000_Single(
                mount=mount,
                tip_racks=[tip_rack])
        return pipette

    # labware setup
    labware.load('opentrons-tuberack-2ml-eppendorf', '1')
    labware.load('opentrons-tuberack-2ml-screwcap', '2')
    trough = labware.load('trough-12row', '3')

    # instrument setup
    pipette_l = mount_pipette(left_pipette, 'left', '5')
    pipette_r = mount_pipette(right_pipette, 'right', '6')

    # destination
    mastermix_dest = trough.wells('A1')

    info_list = [cell for line in master_mix_csv.splitlines() if line
                 for cell in [line.split(',')]]

    for line in info_list[1:]:
        source = robot.deck.children_by_name[line[1]][0].wells(line[2])
        vol = float(line[3])
        if vol < pipette_r.min_volume and vol > pipette_l.min_volume:
            pipette = pipette_l
        else:
            pipette = pipette_r
        pipette.transfer(vol, source, mastermix_dest)
