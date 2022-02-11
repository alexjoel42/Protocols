import os
import json

# metadata
metadata = {
    'protocolName': 'Redo Replacement Picking (Greiner Masterblock 384 Well \
Plate 225 µL)',
    'author': 'Nick <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.11'
}


def run(ctx):

    tip_track = True

    [input_file, tuberack_scan, plate_scan, default_disposal_vol,
     default_transfer_vol, p300_mount] = get_values(  # noqa: F821
        'input_file', 'tuberack_scan', 'plate_scan', 'default_disposal_vol',
        'default_transfer_vol', 'p300_mount')

    # load labware
    rack = ctx.load_labware('eurofins_96x2ml_tuberack', '2', 'tuberack')
    plate = ctx.load_labware('greinermasterblock_384_wellplate_225ul', '1')
    tips300 = [
        ctx.load_labware('opentrons_96_tiprack_300ul', slot)
        for slot in ['11']]

    # pipette
    p300 = ctx.load_instrument('p300_single_gen2', p300_mount,
                               tip_racks=tips300)

    tip_log = {val: {} for val in ctx.loaded_instruments.values()}

    folder_path = '/data/tip_track'
    tip_file_path = folder_path + '/tip_log.json'
    if tip_track and not ctx.is_simulating():
        if os.path.isfile(tip_file_path):
            with open(tip_file_path) as json_file:
                data = json.load(json_file)
                for pip in tip_log:
                    if pip.name in data:
                        tip_log[pip]['count'] = data[pip.name]
                    else:
                        tip_log[pip]['count'] = 0
        else:
            for pip in tip_log:
                tip_log[pip]['count'] = 0
    else:
        for pip in tip_log:
            tip_log[pip]['count'] = 0

    for pip in tip_log:
        if pip.type == 'multi':
            tip_log[pip]['tips'] = [tip for rack in pip.tip_racks
                                    for tip in rack.rows()[0]]
        else:
            tip_log[pip]['tips'] = [tip for rack in pip.tip_racks
                                    for tip in rack.wells()]
        tip_log[pip]['max'] = len(tip_log[pip]['tips'])

    def _pick_up(pip, loc=None):
        if tip_log[pip]['count'] == tip_log[pip]['max'] and not loc:
            ctx.pause('Replace ' + str(pip.max_volume) + 'µl tipracks before \
resuming.')
            pip.reset_tipracks()
            tip_log[pip]['count'] = 0
        if loc:
            pip.pick_up_tip(loc)
        else:
            pip.pick_up_tip(tip_log[pip]['tips'][tip_log[pip]['count']])
            tip_log[pip]['count'] += 1

    # check barcode scans (tube, plate)
    tuberack_bar, plate_bar = input_file.splitlines()[3].split(',')[:2]
    if not tuberack_scan[:len(tuberack_scan)-4] == tuberack_bar.strip():
        print(tuberack_scan[:len(tuberack_scan)-4])
        raise Exception(f'Tuberack scans do not match ({tuberack_bar}, \
{tuberack_scan})')
    if not plate_scan[:len(plate_scan)-4] == plate_bar.strip():
        raise Exception(f'Plate scans do not match ({plate_bar}, {plate_bar})')

    # parse
    data = [
        [val.strip() for val in line.split(',')]
        for line in input_file.splitlines()[4:]
        if line and line.split(',')[0].strip()]

    tubes_ordered = [
        well for i in range(2) for col in rack.columns()
        for well in col[i*8:(i+1)*8]]

    for line in data:
        tube = tubes_ordered[int(line[0])-1]
        well = plate.wells()[int(line[1])-1]
        if len(line) >= 3 and line[2]:
            disposal_vol = float(line[2])
        else:
            disposal_vol = default_disposal_vol
        if len(line) >= 4 and line[3]:
            transfer_vol = float(line[3])
        else:
            transfer_vol = default_transfer_vol

        # remove contents of well
        p300.pick_up_tip()
        ctx.max_speeds['A'] = 100  # slow descent
        ctx.max_speeds['Z'] = 100  # slow descent

        p300.aspirate(disposal_vol, well.bottom(0.2))
        del ctx.max_speeds['A']  # reset to default
        del ctx.max_speeds['Z']  # reset to default
        p300.drop_tip()

        # transfer tube to well
        p300.transfer(transfer_vol, tube.bottom(0.5), well.top(-1))

    # track final used tip
    if not ctx.is_simulating():
        if not os.path.isdir(folder_path):
            os.mkdir(folder_path)
        data = {pip.name: tip_log[pip]['count'] for pip in tip_log}
        with open(tip_file_path, 'w') as outfile:
            json.dump(data, outfile)