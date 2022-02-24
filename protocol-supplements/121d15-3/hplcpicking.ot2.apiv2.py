import os
import json

# metadata
metadata = {
    'protocolName': 'HPLC Picking',
    'author': 'Nick <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.11'
}


def run(ctx):

    tip_track = True

    # load labware
    rack = ctx.load_labware('eurofins_96x2ml_tuberack', '2', 'tuberack')
    plates = [
        ctx.load_labware('irishlifesciences_96_wellplate_2200ul', slot,
                         f'plate {i+1}')
        for i, slot in enumerate(['10', '7', '4', '1'])]
    tips300 = [ctx.load_labware('opentrons_96_tiprack_300ul', '11')]

    # pipette
    p300 = ctx.load_instrument('p300_single_gen2', 'left',
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

    # parse
    data = [
        line.split(',') for line in INPUT_FILE.splitlines()
        if line and line.split(',')[0].strip()]

    # order
    wells_ordered = [
        well for plate in plates for row in plate.rows() for well in row]

    # determine plates in use
    plates_used = {key: False for key in range(4)}
    for i, line in enumerate(data):
        source = wells_ordered[int(line[0]) - 1]
        plates_used[source//96] = True

    if not plates_used[3]:
        plates = [
            ctx.load_labware('irishlifesciences_96_wellplate_2200ul', slot,
                             f'plate {i+1}')
            for i, slot in enumerate(['10', '7', '4'])]
        water = ctx.load_labware('test_1_reservoir_300000ul', '1').wells()[0]
    else:
        plates = [
            ctx.load_labware('irishlifesciences_96_wellplate_2200ul', slot,
                             f'plate {i+1}')
            for i, slot in enumerate(['10', '7', '4', '1'])]
        water = plates[-1].wells_by_name()['D6']

    dest_vols = {}
    prev_dest = None
    for i, line in enumerate(data):
        source = wells_ordered[int(line[0]) - 1]
        dest = rack.wells_by_name()[line[1].upper()]
        if len(line) > 2 and line[2]:
            vol = round(float(line[2]))
        else:
            vol = DEFAULT_TRANSFER_VOL

        # check for volumes slightly over 300ul from HPLC input files
        vol = 300 if 300 < vol < 305 else vol

        if dest != prev_dest:
            if p300.has_tip:
                p300.drop_tip()
            _pick_up(p300)
        p300.transfer(vol, source.bottom(0.5), dest.top(-1), new_tip='never')
        p300.blow_out(dest)
        p300.touch_tip(dest)
        prev_dest = dest

        # track volumes for final adjustment
        if dest not in dest_vols:
            dest_vols[dest] = vol
        else:
            dest_vols[dest] += vol
    p300.drop_tip()

    # final adjustment with water up to 1500ul
    ctx.pause('Replace plate 4 in slot 1 with water reservoir. Resume once \
finished.')
    water = plates[-1].wells_by_name()['D4'].bottom(1)
    p300.pick_up_tip()
    for tube, vol in dest_vols.items():
        adjustment = 1500 - vol
        if adjustment > 0:
            p300.transfer(adjustment, water, tube.top(-1), new_tip='never')
            p300.blow_out(tube)
            p300.touch_tip(tube)
    p300.drop_tip()

    # track final used tip
    if not ctx.is_simulating():
        if not os.path.isdir(folder_path):
            os.mkdir(folder_path)
        data = {pip.name: tip_log[pip]['count'] for pip in tip_log}
        with open(tip_file_path, 'w') as outfile:
            json.dump(data, outfile)
