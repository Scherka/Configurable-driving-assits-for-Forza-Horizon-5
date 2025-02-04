import pygame
import vgamepad as vg
import time
from controller_modifier import adjust_input

controller = None

buttons = {
    0: vg.XUSB_BUTTON.XUSB_GAMEPAD_A,
    1: vg.XUSB_BUTTON.XUSB_GAMEPAD_B,
    2: vg.XUSB_BUTTON.XUSB_GAMEPAD_X,
    3: vg.XUSB_BUTTON.XUSB_GAMEPAD_Y,
    4: vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER,
    5: vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER,
    6: vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK,
    7: vg.XUSB_BUTTON.XUSB_GAMEPAD_START,
    8: vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB,
    9: vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB
    }
def map_inputs_to_virtual(toggle_tcr_queue, gamepad, inputs, coeff_rt):
    """
    Map inputs from a real controller to a virtual controller.
    """
    for event in pygame.event.get():
        # if event.type == pygame.JOYBUTTONDOWN:  # Button press
        #     gamepad.press_button(buttons[event.button])
        # #     print(buttons[event.button])
        # elif event.type == pygame.JOYBUTTONUP:  # Button release
        #      gamepad.release_button(buttons[event.button])
        if event.type == pygame.JOYHATMOTION:
            if event.value[0] == 1:
                gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT)
            elif event.value[0] == -1:
                gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT)
            elif event.value[1] == 1:
                gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP)
            elif event.value[1] == -1:
                gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN)
                toggle_tcr_queue.put(True)
            if event.value[0] == 0:
                gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT)
                gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT)
            if event.value[1] == 0:
                gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP)
                gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN)
        elif event.type == pygame.JOYAXISMOTION:  # Stick or trigger motion
            if event.axis == 0:  # Left stick X
                inputs['left_x'] = event.value
            elif event.axis == 1:  # Left stick X
                inputs['left_y'] = event.value
            elif event.axis == 2:  # Right stick X
                inputs['right_x'] = event.value
            elif event.axis == 3:  # Right stick X
                inputs['right_y'] = event.value
            elif event.axis == 4:  # Left trigger
                inputs['lt'] = (event.value + 1) / 2
            elif event.axis == 5:  # Right trigger
                inputs['rt'] = (event.value + 1) / 2
        gamepad.left_trigger_float(inputs['lt'])
        gamepad.right_trigger_float(inputs['rt']*coeff_rt)
        gamepad.left_joystick(int(inputs['left_x'] * 32767), -int(inputs['left_y'] * 32766))
        gamepad.right_joystick(int(inputs['right_x'] * 32767), -int(inputs['right_y'] * 32766))

    gamepad.update()
    return inputs



def virtual_controller(queue, toggle_tcr_queue, controller_index):
    # Initialize pygame
    pygame.init()

    global controller
    controller = pygame.joystick.Joystick(controller_index)
    controller.init()
    print(f"Using controller: {controller.get_name()}")
    gamepad = vg.VX360Gamepad()

    # Inputs for the virtual controller
    inputs = {'left_x': 0, 'left_y': 0, 'right_x': 0, 'right_y': 0, 'rt': 0, 'lt':0}
    # If TCR is disabled, coefficient is 1
    telemetry_data = (1, "forced")
    # Previous telemetry for detecting start of movement or gear change
    previous_telemetry_data = telemetry_data
    # Coefficient that applies to the right trigger
    coefficient_rt = 1 # 1 means no change to user's input
    try:
        while True:
            while not queue.empty():
                telemetry_data = queue.get()
            # receive telemetry, adjust coefficient and send it to the virtual controller
            coefficient_rt = adjust_input(telemetry_data, previous_telemetry_data, coefficient_rt)
            previous_telemetry_data = telemetry_data
            inputs = map_inputs_to_virtual(toggle_tcr_queue, gamepad, inputs, coefficient_rt)
            time.sleep(0.01)  # Avoid high CPU usage
    except KeyboardInterrupt:
        print("Exiting...")

