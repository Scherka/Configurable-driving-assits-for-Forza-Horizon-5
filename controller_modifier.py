import resources
# Read telemetry and decrease/increase the right trigger coefficient to regain grip
def adjust_to_slip(telemetry_data, coeff_rt):
    rear_right = telemetry_data["TireCombinedSlipRearRight"]
    rear_left = telemetry_data["TireCombinedSlipRearLeft"]
    front_right = telemetry_data["TireCombinedSlipFrontRight"]
    front_left = telemetry_data["TireCombinedSlipFrontLeft"]
    drivetrain = telemetry_data["DriveTrainType"]
    threshold = telemetry_data["Threshold"]
    drop_rate = telemetry_data["DropRate"]
    minimum_coefficient = telemetry_data["MinimumCoefficient"]
    tires_for_check = []

    # To start reducing the coefficient, all tires of drive axle(s) must be over the threshold
    if drivetrain in [resources.drivetrains['AWD'], resources.drivetrains['RWD']]:
        tires_for_check.append(rear_right)
        tires_for_check.append(rear_left)
    if drivetrain in [resources.drivetrains['AWD'], resources.drivetrains['FWD']]:
        tires_for_check.append(front_right)
        tires_for_check.append(front_left)
    if all(tire > threshold for tire in tires_for_check):
        return max(minimum_coefficient, coeff_rt * (1-drop_rate))
    else:
        return min(1, coeff_rt / (1-drop_rate))

#
def adjust_input(telemetry_data,previous_telemetry_data, coeff_rt):
    # launch control works only if the car wasn't moving
    if telemetry_data[1] == 'lc':
        started_moving = previous_telemetry_data[1] != 'lc' or previous_telemetry_data[0]["Speed"] * 3.6 < 0.1
    else:
        started_moving = False
    if telemetry_data[1] in ['lc', 'tcr']:
        current_gear = telemetry_data[0]["Gear"]
        if previous_telemetry_data[1] not in ['tcr', 'lc'] or previous_telemetry_data[0]["Gear"] == current_gear \
                and not started_moving:
            # If gear hasn't been changed, adjust the right trigger coefficient according to the current grip
            coeff_rt = adjust_to_slip(telemetry_data[0], coeff_rt)
        else:
            # When changing gear, the right trigger coefficient is decreased to maintain grip
            coeff_rt = telemetry_data[0]["MinimumCoefficient"] + 0.05 * (current_gear - 1)
    elif telemetry_data[1] == 'forced':
        # If forced coefficient is enabled, the right trigger coefficient is set to the forced coefficient
        coeff_rt = telemetry_data[0]
    return coeff_rt