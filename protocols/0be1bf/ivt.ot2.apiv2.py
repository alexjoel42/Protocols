import math

metadata = {
    'protocolName': 'IVT Aliquots',
    'author': 'Nick Diehl <ndiehl@opentrons.com>',
    'apiLevel': '2.14'
}

rxn_vol = 500.0
factor_overage = 1.1
concentration_target = 0.1


def run(ctx):

    [num_rxns, concentration_template] = get_values(  # noqa: F821
        'num_rxns', 'concentration_template')

    # labware
    mix_rack = ctx.load_labware(
        'opentrons_24_tuberack_eppendorf_2ml_safelock_snapcap',
        '4', 'component rack')
    rack15 = ctx.load_labware(
        'opentrons_15_tuberack_5000ul', '8', 'mix tube')
    aliquot_rack = ctx.load_labware(
        'opentrons_24_tuberack_eppendorf_2ml_safelock_snapcap',
        '5', 'aliquot rack')
    reservoir = ctx.load_labware('nest_12_reservoir_15ml', '6', 'reservoir')
    tiprack_20 = [ctx.load_labware('opentrons_96_tiprack_20ul', '1')]
    tiprack_300 = [ctx.load_labware('opentrons_96_tiprack_300ul', '2')]

    template_vol = round(rxn_vol*concentration_target/concentration_template,
                         2)
    mix_volumes = [
        20.0, 1.0, 35.0, 35.0, 35.0, 35.0, 20.0, 16.0, 2.5, 5.0, template_vol]
    mix_map = {
        well: vol
        for well, vol in zip(mix_rack.wells()[:len(mix_volumes)], mix_volumes)
    }
    enzyme_volumes = [25, 0.1]
    enzyme_map = {
        well: vol
        for well, vol in zip(
            mix_rack.wells()[len(mix_volumes):len(mix_volumes)+2],
            enzyme_volumes)
    }

    colors = [
        '#5b3811',
        '#ddb4ca',
        '#4f3e24',
        '#584582',
        '#860916',
        '#1f6f7e',
        '#95bb6d',
        '#f5ea87',
        '#539a51',
        '#992d16',
        '#5f50cf',
        '#159668',
        '#897f77',
        '#2bad24',
        '#3bbac0',
        '#44971e',
        '#d11e7f',
        '#4cfe77',
        '#ee06d2',
        '#9ffd59']

    for letter, (well, vol) in zip('ABCDEFGHIJK', mix_map.items()):

        temp = ctx.define_liquid(
            name=letter,
            description='',
            display_color=colors.pop()
        )
        well.load_liquid(temp, vol*num_rxns*1.1)

    for letter, (well, vol) in zip(['TP', 'P'], enzyme_map.items()):

        temp = ctx.define_liquid(
            name=letter,
            description='',
            display_color=colors.pop()
        )
        well.load_liquid(temp, vol*num_rxns*1.1)

    mix_tube = rack15.wells()[0]
    enzyme_mix_tube = mix_rack.rows()[0][-1]
    dn = mix_rack.wells()[len(mix_volumes)+2]
    cac = mix_rack.wells()[len(mix_volumes)+3]
    rxns = aliquot_rack.wells()[:num_rxns]
    water = reservoir.wells()[0]
    licl_h2o = reservoir.wells()[1]

    [vol_dn, vol_cac] = [8, 2]

    mix_tube_liq = ctx.define_liquid(
            name='mix tube',
            description='non-enzyme mix components',
            display_color=colors.pop()
    )
    enzyme_mix_tube_liq = ctx.define_liquid(
            name='enzyme mix tube',
            description='enzyme mix components',
            display_color=colors.pop()
    )
    water_liq = ctx.define_liquid(
            name='water',
            description='',
            display_color=colors.pop()
    )
    licl_h2o_liq = ctx.define_liquid(
            name='LiCl + H2O',
            description='1:1 ratio of LiCl and H2O',
            display_color=colors.pop()
    )

    mix_tube.load_liquid(mix_tube_liq, 0)
    enzyme_mix_tube.load_liquid(enzyme_mix_tube_liq, 0)

    dn_liq = ctx.define_liquid(
        name='DN',
        description='',
        display_color=colors.pop()
    )
    dn.load_liquid(dn_liq, vol_dn)

    cac_liq = ctx.define_liquid(
        name='CaC',
        description='',
        display_color=colors.pop()
    )
    cac.load_liquid(cac_liq, vol_cac)

    vol_water = rxn_vol - (sum(mix_volumes) + sum(enzyme_volumes))
    vol_licl_h2o = (rxn_vol + sum([vol_dn, vol_cac]))*2

    water.load_liquid(water_liq, vol_water)
    licl_h2o.load_liquid(licl_h2o_liq, vol_licl_h2o)

    # pipettes
    p300 = ctx.load_instrument(
        'p300_single_gen2', 'left', tip_racks=tiprack_300)
    p20 = ctx.load_instrument(
        'p20_single_gen2', 'right', tip_racks=tiprack_20)

    def slow_withdraw(pip, well, delay_seconds=1.0):
        pip.default_speed /= 10
        if delay_seconds > 0:
            ctx.delay(seconds=delay_seconds)
        pip.move_to(well.top())
        pip.default_speed *= 10

    # initial mix
    for i, (well, vol) in enumerate(mix_map.items()):
        transfer_vol = vol*num_rxns*factor_overage
        pip = p300 if transfer_vol > 20 else p20
        num_trans = math.ceil(
            transfer_vol/pip.tip_racks[0].wells()[0].max_volume)
        vol_per_trans = round(transfer_vol/num_trans, 2)
        pip.pick_up_tip()
        for i in range(num_trans):
            pip.aspirate(vol_per_trans, well.bottom(1.0))
            slow_withdraw(pip, well)
            if i < num_trans - 1:
                pip.dispense(pip.current_volume, mix_tube.top())
            else:
                pip.dispense(pip.current_volume, mix_tube.bottom(2))
                slow_withdraw(pip, mix_tube)
            slow_withdraw(pip, mix_tube)
        if i == len(mix_map.items()) - 1:
            pip.mix(5, pip.max_volume*0.8, mix_tube)
            slow_withdraw(pip, mix_tube)
        pip.drop_tip()

    # enzyme mix
    for i, (well, vol) in enumerate(enzyme_map.items()):
        transfer_vol = vol*num_rxns*factor_overage
        pip = p300 if transfer_vol > 20 else p20
        num_trans = math.ceil(
            transfer_vol/pip.tip_racks[0].wells()[0].max_volume)
        vol_per_trans = round(transfer_vol/num_trans, 2)
        pip.pick_up_tip()
        for _ in range(num_trans):
            pip.aspirate(vol_per_trans, well.bottom(1.0))
            slow_withdraw(pip, well)
            pip.dispense(pip.current_volume, enzyme_mix_tube.bottom(3))
            slow_withdraw(pip, enzyme_mix_tube)
        if i == len(enzyme_map.items()) - 1:
            pip.mix(5, pip.max_volume*0.8, enzyme_mix_tube)
            slow_withdraw(pip, enzyme_mix_tube)
        pip.drop_tip()

    # water addition
    pip = p300 if vol_water >= 20 else p20
    num_trans = math.ceil(vol_water/pip.tip_racks[0].wells()[0].max_volume)
    vol_per_trans = round(vol_water/num_trans, 2)
    pip.pick_up_tip()
    for d in rxns:
        for _ in range(num_trans):
            pip.aspirate(vol_per_trans, water)
            slow_withdraw(pip, water)
            pip.dispense(pip.current_volume, d.bottom(2))
            slow_withdraw(pip, d)
    pip.drop_tip()

    # mix addition
    vol_mix = sum(mix_volumes)
    pip = p300 if vol_mix >= 20 else p20
    num_trans = math.ceil(vol_mix/pip.tip_racks[0].wells()[0].max_volume)
    vol_per_trans = round(vol_mix/num_trans, 2)
    for d in rxns:
        pip.pick_up_tip()
        for _ in range(num_trans):
            pip.aspirate(vol_per_trans, mix_tube)
            slow_withdraw(pip, mix_tube)
            pip.dispense(pip.current_volume, d.bottom(2))
            slow_withdraw(pip, d)
        pip.drop_tip()

    ctx.pause('Place enzymes in tuberack.')

    # enzyme mix addition
    vol_enzyme_mix = sum(enzyme_volumes)
    pip = p300 if vol_enzyme_mix >= 20 else p20
    num_trans = math.ceil(
        vol_enzyme_mix/pip.tip_racks[0].wells()[0].max_volume)
    vol_per_trans = round(vol_enzyme_mix/num_trans, 2)
    for d in rxns:
        pip.pick_up_tip()
        for _ in range(num_trans):
            pip.aspirate(vol_per_trans, enzyme_mix_tube)
            slow_withdraw(pip, enzyme_mix_tube)
            pip.dispense(pip.current_volume, d.bottom(2))
            slow_withdraw(pip, d)
        pip.drop_tip()

    ctx.pause('INCUBATION')

    # DN and CaC
    for vol, reagent in zip([vol_dn, vol_cac], [dn, cac]):
        pip = p20 if vol < 20 else p300
        for d in rxns:
            pip.pick_up_tip()
            pip.aspirate(vol, reagent)
            slow_withdraw(pip, reagent)
            pip.dispense(vol, d)
            slow_withdraw(pip, d)
            pip.drop_tip()

    ctx.pause('INCUBATION')

    # LiCl and H2O
    pip = p300 if vol_licl_h2o >= 20 else p20
    vol_pre_airgap = 20.0
    num_trans = math.ceil(
        vol_licl_h2o/(pip.tip_racks[0].wells()[0].max_volume - vol_pre_airgap))
    vol_per_trans = round(vol_licl_h2o/num_trans, 2)
    for d in rxns:
        pip.pick_up_tip()
        for i in range(num_trans):
            pip.aspirate(vol_pre_airgap, licl_h2o.top())
            pip.aspirate(vol_per_trans, licl_h2o)
            slow_withdraw(pip, licl_h2o)
            if i < num_trans - 1:
                pip.dispense(pip.current_volume, d.top(-1))
                pip.blow_out()
                ctx.delay(seconds=2.0)
            else:
                pip.dispense(pip.current_volume, d.bottom(2))
                slow_withdraw(pip, d)
        pip.drop_tip()