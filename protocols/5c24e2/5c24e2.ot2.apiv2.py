metadata = {
    'protocolName': 'Plate Filling Sample in AB 384 Well Plate',
    'author': 'Chaz <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.5'
}


def run(protocol):
    [p20mnt, sec_plate] = get_values(  # noqa: F821
    'p20mnt', 'sec_plate')

    # load labware and pipettes
    tips = [
        protocol.load_labware(
            'opentrons_96_tiprack_20ul', s) for s in range(1, 11, 3)]
    pip = protocol.load_instrument('p20_multi_gen2', p20mnt, tip_racks=tips)
    dnaPlates = [
        protocol.load_labware(
            'nest_96_wellplate_100ul_pcr_full_skirt',
            s) for s in range(2, 12, 3)]

    mmPlates = [
        protocol.load_labware(
            'appliedbiosystemsmicroampoptical384' +
            'wellreactionplatewithbarcode_384_wellplate_30ul',
            s) for s in ['3', '6']]
    plate1 = [mmPlates[0][ltr+str(i)] for i in range(1, 13) for ltr in 'AB']
    plate2 = [mmPlates[0][ltr+str(i)] for i in range(13, 25) for ltr in 'AB']
    plate3 = [mmPlates[1][ltr+str(i)] for i in range(1, 13) for ltr in 'AB']
    plate4 = [mmPlates[1][ltr+str(i)] for i in range(13, 25) for ltr in 'AB']

    for s_plate, d_plate in zip(dnaPlates[:2], [plate1, plate2]):
        dest1 = d_plate[::2]
        dest2 = d_plate[1::2]
        for src, d1, d2 in zip(s_plate.rows()[0], dest1, dest2):
            pip.pick_up_tip()
            pip.aspirate(5, src)
            pip.dispense(2.5, d1)
            pip.dispense(2.5, d2)
            pip.drop_tip()

    if sec_plate == 'yes':
        for s_plate, d_plate in zip(dnaPlates[2:], [plate3, plate4]):
            dest1 = d_plate[::2]
            dest2 = d_plate[1::2]
            for src, d1, d2 in zip(s_plate.rows()[0], dest1, dest2):
                pip.pick_up_tip()
                pip.aspirate(5, src)
                pip.dispense(2.5, d1)
                pip.dispense(2.5, d2)
                pip.drop_tip()
