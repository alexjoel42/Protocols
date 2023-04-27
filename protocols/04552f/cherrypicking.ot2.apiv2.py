from opentrons import protocol_api

metadata = {
    'protocolName': 'Cherrypicking',
    'author': 'Nick <ndiehl@opentrons.com>',
    'apiLevel': '2.13'
}


def run(ctx):

    [input_csv, mount_p300, mount_p20] = get_values(  # noqa: F821
        'input_csv', 'mount_p300', 'mount_p20')

    source_plates = [
        ctx.load_labware('corning_384_wellplate_112ul_flat', slot,
                         f'original plate {i+1}')
        for i, slot in enumerate(['1', '4'])]
    dest_plates = [
        ctx.load_labware('corning_384_wellplate_112ul_flat', slot,
                         f'destination plate {i+1}')
        for i, slot in enumerate(['2', '5'])]
    tipracks_20 = [
        ctx.load_labware('opentrons_96_tiprack_20ul', slot)
        for slot in ['3', '6', '9']]
    tipracks_300 = [
        ctx.load_labware('opentrons_96_tiprack_300ul', slot)
        for slot in ['7', '8', '11']]
    tuberack50 = ctx.load_labware(
        'opentrons_6_tuberack_falcon_50ml_conical', '10')

    p20 = ctx.load_instrument(
        'p20_single_gen2', mount_p20, tip_racks=tipracks_20)
    p300 = ctx.load_instrument(
        'p300_single_gen2', mount_p300, tip_racks=tipracks_300)

    media_liquid = ctx.define_liquid(
        name='media',
        description='media',
        display_color='#00FF00',
    )
    media = tuberack50.wells()[0]
    media.load_liquid(media_liquid, 25000)

    data = [
        line.split(',')
        for line in input_csv.splitlines()[1:] if line]

    def pick_up(pip):
        try:
            pip.pick_up_tip()
        except protocol_api.labware.OutOfTipsError:
            ctx.pause(f'Replace {pip} tipracks, slots \
{",".join([rack.parent for rack in pip.tip_racks])} before resuming.')
            pip.reset_tipracks()
            pip.pick_up_tip()

    def slow_withdraw(pip, well, delay_seconds=1.0):
        pip.default_speed /= 10
        if delay_seconds > 0:
            ctx.delay(seconds=delay_seconds)
        pip.move_to(well.top())
        pip.default_speed *= 10

    last_source_lw = None
    last_dest_lw = None
    media_sources = []
    media_dests = []
    for i, line in enumerate(data):
        source_ind = (int(line[0].split('.')[-1]) - 1) % 2
        dest_ind = (int(line[3].split('.')[-1]) - 1) % 2

        source_labware = source_plates[source_ind]
        source_well = source_labware.wells_by_name()[line[1]]
        vol_picking = float(line[2])
        dest_labware = dest_plates[dest_ind]
        dest_well = dest_labware.wells_by_name()[line[4]]
        vol_seeding = float(line[5])
        # vol_trashing = float(line[6])
        vol_media_s = float(line[7])
        vol_media_d = float(line[8])
        pip = p300 if vol_picking >= 20 else p20

        # check for media
        media_bool = False
        if i > 0 and last_source_lw != source_labware:
            media_bool = True
            sources = [media_source[0] for media_source in media_sources]
            vols = [media_source[1] for media_source in media_sources]
            pick_up(p300)
            p300.distribute(vols, media, [s.top() for s in sources],
                            new_tip='never')
            ctx.pause(f'Plate {source_plates.index(source_labware)+1} \
finished. Load new plate if necessary.')
        if i > 0 and last_dest_lw != dest_labware:
            media_bool = True
            dests = [media_dest[0] for media_dest in media_dests]
            vols = [media_dest[1] for media_dest in media_dests]
            if not p300.has_tip:
                pick_up(p300)
            p300.distribute(vols, media, [d.top(-1) for d in dests],
                            new_tip='never')
            ctx.comment(f'Plate {dest_plates.index(dest_labware)+1} \
finished. Load new plate if necessary.')
        if p300.has_tip:
            p300.drop_tip()

        last_source_lw = source_labware
        last_dest_lw = dest_labware

        if media_bool:
            media_sources = []
            media_dests = []

        pick_up(pip)
        pip.mix(3, 20, source_well.bottom(1))
        pip.aspirate(vol_picking, source_well.bottom(1))
        slow_withdraw(pip, source_well)
        pip.dispense(vol_seeding, dest_well)
        slow_withdraw(pip, dest_well)
        pip.blow_out(pip.trash_container.wells()[0])
        pip.return_tip()

        media_sources.append([source_well, vol_media_s])
        media_dests.append([dest_well, vol_media_d])

    # fill last wells if necessary
    remaining_media_wells = media_sources + media_dests
    if len(remaining_media_wells) > 0:
        wells = [well_set[0] for well_set in remaining_media_wells]
        vols = [well_set[1] for well_set in remaining_media_wells]
        pick_up(p300)
        p300.distribute(vols, media, wells, new_tip='never')
        p300.drop_tip()