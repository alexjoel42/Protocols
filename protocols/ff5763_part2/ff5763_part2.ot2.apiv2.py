"""OPENTRONS."""
import math
from opentrons.types import Point
metadata = {
    'protocolName': 'Protocol Title',
    'author': 'AUTHOR NAME <authoremail@company.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.11'   # CHECK IF YOUR API LEVEL HERE IS UP TO DATE
                         # IN SECTION 5.2 OF THE APIV2 "VERSIONING"
}


def run(ctx):
    """PROTOCOL."""
    [
     num_samples
    ] = get_values(  # noqa: F821 (<--- DO NOT REMOVE!)
        "num_samples")

    # define all custom variables above here with descriptions:

    # number of samples
    num_cols = math.ceil(num_samples/8)

    # "True" for park tips, "False" for discard tips

    # load modules/labware
    """Step 2 has the sample plate on the mag module in slot 4!"""
    temp_1 = ctx.load_module('tempdeck', '1')
    thermo_tubes = temp_1.load_labware('opentrons_96_aluminumblock_generic_pcr'
                                       '_strip_200ul')
    mag_module = ctx.load_module('magnetic module gen2', '4')
    sample_plate = mag_module.load_labware('nest_96_wellplate_100ul_pcr'
                                           '_full_skirt')
    reagent_resv = ctx.load_labware('nest_12_reservoir_15ml', '5')
    liquid_trash = ctx.load_labware('nest_1_reservoir_195ml', '9')

    # load tipracks
    tiprack20 = [ctx.load_labware('opentrons_96_filtertiprack_20ul', slot)
                 for slot in ['3']]
    tiprack200 = [ctx.load_labware('opentrons_96_filtertiprack_200ul', slot)
                  for slot in ['6']]

    # load instrument
    m20 = ctx.load_instrument('p20_multi_gen2', 'right', tip_racks=tiprack20)
    m300 = ctx.load_instrument('p300_multi_gen2', 'left', tip_racks=tiprack200)

    # reagents
    '''includes reagents used in other steps for housekeeping purposes'''
    master_mix = thermo_tubes.rows()[0][0]
    nf_water = thermo_tubes.rows()[0][1]
    tsb = thermo_tubes.rows()[0][2]
    twb = reagent_resv.wells()[0]
    sample_dest = sample_plate.rows()[0][:num_cols]
    pcr_mix = reagent_resv.wells()[1]

    # protocol

    # Slowly add 10ul TSB (beads) then slowly mix to suspend
    for dest in sample_dest:
        m20.pick_up_tip()
        m20.aspirate(10, tsb)
        m20.flow_rate_dispense = 3
        m20.dispense(10, dest)
        m20.drop_tip()

    for dest in sample_dest:
        m300.pick_up_tip()
        m300.flow_rate_aspirate = 30
        m300.flow_rate_dispense = 30
        m300.mix(10, 55, dest)
        m300.drop_tip()
    ctx.pause("""Please move sample plate from slot 4"""
              """to off-deck thermocycler then return to magnetic module"""
              """in slot 4 for purification. Click 'Resume' when set""")

    """"insert mag module purification base code here"""
    # Incubate on mag stand, 3 minutes

    # Remove supernatant
    for s in sample_dest:
        m300.pick_up_tip()
        # going to break transfer func up for better control
        m300.transfer(65, s.bottom(1), liquid_trash[0], new_tip='never')
        m300.blow_out()
        m300.drop_tip()
    # Wash twice like this:
    # disengage mag
    # add 100ul TWB slowly onto beads
    # slowly mix to resuspend
    # engage mag
    # incubate 3 min on mag stand until clear
    # remove supernatant
    # TWB washes 2x
    # Disengage mag
    # Slowly add 100ul TWB onto beads
    # slowly mix to resuspend
    count = 0
    total_twb = 100
    for wash in range(3):
        mag_module.disengage()

        # resuspend beads in TWB
        for i, s in sample_dest:
            ind = (count*len(twb))//total_twb
            count += 1

            side = i % 2
            angle = 1 if side == 0 else -1
            disp_loc = s.bottom().move(
                Point(x=0.85*(s.diameter/2)*angle, y=0, z=3))
            m300.pick_up_tip()
            m300.aspirate(100, twb[ind])
            m300.move_to(s.center())
            # add pipette rate slow here (half speed)
            m300.dispense(100, disp_loc)
            m300.mix(10, 80, disp_loc)
            m300.drop_tip()

        mag_module.engage(height=18)

        if wash < 2:
            ctx.delay(
                minutes=3, msg='Incubating beads on magnet for 3 minutes')
            # remove and discard supernatant
            for s in sample_dest:
                m300.pick_up_tip()
                # going to break transfer func up for better control options
                m300.transfer(
                    120, s.bottom(1), liquid_trash[wash], new_tip='never')
                m300.blow_out()
                m300.drop_tip()

    # End part 2
    for c in ctx.commands():
        print(c)