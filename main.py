import sys
import pygame
import virtual_controller
from PyQt5 import QtCore, QtWidgets
from interface import Ui_MainWindow
from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QLineEdit, QPushButton, QCheckBox, QMessageBox
from PyQt5.QtCore import Qt, QTimer
from multiprocessing import Process, Queue
from telemetry import udp_listener  # Import the UDP listener function
from acceleration import calculate_acceleration_time  # Import the acceleration function

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, telemetry_queue, controller_modifier_queue, toggle_tcr_queue, acceleration_time_queue):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self) # set up the window from the interface.py
        self.configure_logic() # connect widgets to relevant functions
        self.load_config() # load data from config
        self.telemetry_queue = telemetry_queue  # Queue for telemetry data
        self.controller_modifier_queue = controller_modifier_queue  # Queue for controller modifier data
        self.toggle_tcr_queue = toggle_tcr_queue  # Queue for signals from input device
        self.acceleration_time_queue = acceleration_time_queue  # Queue for acceleration time data
        self.get_gamepads() # get list of gamepads
        self.tcr = False # True if traction control is enabled
        self.tcr_forced = False # True if forced coefficient is enabled
        self.first_run = True # True if first run
        self.virtual_controller = False # True if virtual controller is enabled
        self.lc = False # True if launch control is enabled
        # Map achieved speed to widgets
        self.speed_mapping = {
            '100': self.ui.to_100_time,
            '200': self.ui.to_200_time,
            '300': self.ui.to_300_time,
            '400': self.ui.to_400_time,
            '500': self.ui.to_500_time,
        }
        # Timer
        self.timer = QTimer()
        self.timer.start(10)  # Check the queues every 10ms

    # Load data from config
    def load_config(self):
        try:
            self.forced_coefficient_value = "1"
            self.drop_rate_value = config['tcr_drop_rate']
            self.threshold_value = config['tcr_threshold']
            self.minimum_coefficicient_value = config['tcr_minimum_coefficient']
            self.ui.port_input.setText(config['port'])
            self.ui.drop_rate_input.setText(str(self.drop_rate_value))
            self.ui.current_drop_rate.setText(f"Current: {str(self.drop_rate_value)}")
            self.ui.threshold_input.setText(str(self.threshold_value))
            self.ui.current_threshold.setText(f"Current: {str(self.threshold_value)}")
            self.ui.minimum_coefficient_input.setText(str(self.minimum_coefficicient_value))
            self.ui.current_minimum_coefficient.setText(f"Current: {str(self.minimum_coefficicient_value)}")
            self.ui.forced_coefficient_input.setText(str(self.forced_coefficient_value))
        except Exception as e:
            self.show_warning(str(e))

    # Get list of gamepads and show them in the list
    def get_gamepads(self):
        try:
            self.gamepad_list = []
            for i in range(pygame.joystick.get_count()):
                self.gamepad_list.append(pygame.joystick.Joystick(i).get_name())
            self.ui.gamepad_list.addItems(self.gamepad_list)
            self.ui.gamepad_list.currentIndexChanged.connect(self.change_input_device)
        except Exception as e:
            self.show_warning(str(e))

    # When gamepad is chosen, start the virtual controller
    def change_input_device(self):
        try:
            self.input_device = self.ui.gamepad_list.currentText()
            self.input_device_index = self.ui.gamepad_list.currentIndex()
            print("Input device:", self.input_device_index)
            self.ui.gamepad_list.setEnabled(False)
            self.virtual_controller = True
            global controller_modifier_process
            # Start the controller modifier process
            controller_modifier_process = Process(
                target=virtual_controller.virtual_controller,
                args=(controller_modifier_queue, toggle_tcr_queue, self.input_device_index-1))
            controller_modifier_process.start()
        except Exception as e:
            self.show_warning("Change device: " + str(e))

    # Disable virtual controller
    def disable_virtual_controller(self):
        if self.virtual_controller:
            controller_modifier_process.terminate()
            controller_modifier_process.join()
        self.virtual_controller = False

    # Connect buttons and toggles to relevant functions
    def configure_logic(self):
        self.ui.start_telemetry.clicked.connect(self.start_listening_telemetry)
        self.ui.stop_telemetry.clicked.connect(self.stop_listening_telemetry)
        self.ui.drop_rate_change.clicked.connect(self.change_drop_rate)
        self.ui.threshold_change.clicked.connect(self.change_threshold)
        self.ui.minimum_coefficient_change.clicked.connect(self.change_minimum_coefficient)
        self.ui.toggle_tcr_button.clicked.connect(self.toggle_tcr)
        self.ui.forced_coefficient_checkbox.stateChanged.connect(self.toggle_forced_coefficient)
        self.ui.forced_coefficient_change.clicked.connect(self.change_forced_coefficient)
        self.ui.launch_control_checkbox.stateChanged.connect(self.toggle_launch_control)

    # Start listening telemetry    
    def start_listening_telemetry(self):
        self.stop_listening_telemetry()
        self.ui.stop_telemetry.setEnabled(True)
        self.ui.start_telemetry.setText("Change")
        print("Port:", self.ui.port_input.text())
        port = self.ui.port_input.text()
        self.first_run = False
        try:
            self.turn_on_tcr()
            config['port'] = port
            write_config(config)
            # Convert the port number to an integer
            port = int(port)
            # Start the UDP listener and acceleration time calculator in separate processes
            global listener_process
            global acceleration_time_calculator_process
            listener_process = Process(target=udp_listener, args=(telemetry_queue, speed_queue, port))
            listener_process.start()
            acceleration_time_calculator_process = Process(target=calculate_acceleration_time,
                                                           args=(speed_queue, acceleration_time_queue))
            acceleration_time_calculator_process.start()
            self.timer.timeout.connect(self.check_queue)
        except ValueError:
            print("Invalid port! Please enter a number.")
            self.stop_listening_telemetry()
            self.show_warning("Invalid port! Please enter a number.")
        except Exception as e:
            print(f"An error occurred: {e}")
            self.stop_listening_telemetry()
            self.show_warning(str(e))

    # You won't believe what this function does
    def stop_listening_telemetry(self):
        self.ui.stop_telemetry.setEnabled(False)
        self.ui.start_telemetry.setText("Start")
        try:

            # Stop the UDP listener and acceleration time calculator processes
            if not self.first_run:
                self.timer.timeout.disconnect(self.check_queue)
                if listener_process.is_alive():
                    listener_process.terminate()
                    listener_process.join()
                if acceleration_time_calculator_process.is_alive():
                    acceleration_time_calculator_process.terminate()
                    acceleration_time_calculator_process.join()
        except Exception as e:
            self.show_warning("stop", str(e))
        finally:
            self.turn_off_tcr()

    # Check all queues
    def check_queue(self):
        while not self.telemetry_queue.empty():

            telemetry_data = self.telemetry_queue.get()
            # print(telemetry_data[0])
            if telemetry_data[1] == 'error':
                self.stop_listening_telemetry()
                self.show_warning(f'Error in listener process: {telemetry_data[0]}')
            elif telemetry_data[1] == 'data':
                telemetry_data[0]["Threshold"] = float(self.threshold_value)
                telemetry_data[0]["MinimumCoefficient"] = float(self.minimum_coefficicient_value)
                telemetry_data[0]["DropRate"] = float(self.drop_rate_value)
                # if TCR is enabled, check if forced coefficient is enabled
                if self.tcr:
                    if self.tcr_forced:
                        self.controller_modifier_queue.put((float(self.forced_coefficient_value), "forced"))
                    else:
                        if self.lc:
                            mode = "lc"
                        else:
                            mode = "tcr"
                        self.controller_modifier_queue.put((telemetry_data[0], mode))
                # otherwise, send a forced coefficient of 1 thus no change to user's input
                else:
                    self.controller_modifier_queue.put((1, "forced"))

        # Check the acceleration time and display it
        while not self.acceleration_time_queue.empty():
            acceleration_time_data = self.acceleration_time_queue.get()
            time = acceleration_time_data[0]
            achieved_speed = acceleration_time_data[1]
            if achieved_speed in self.speed_mapping:
                self.speed_mapping[achieved_speed].setText(f'{time:.3f}')
                self.speed_mapping[achieved_speed].setStyleSheet("color: black; font-weight: bold")
        # Check the signals to turn on/off TCR
        while not self.toggle_tcr_queue.empty():
            signal = self.toggle_tcr_queue.get()
            if signal:
                self.toggle_tcr()

    # Turn on/off TCR
    def toggle_tcr(self):
        if self.tcr:
            self.turn_off_tcr()
        else:
            self.turn_on_tcr()

    def turn_on_tcr(self):
        print("TCR ON")
        self.tcr = True
        self.ui.tcr_indicator.setText("TCR ON")
        self.ui.tcr_indicator.setStyleSheet("color: green; font-weight: bold")
        self.ui.toggle_tcr_button.setText("Turn TCR off")
        self.ui.launch_control_checkbox.setEnabled(True)
        self.ui.forced_coefficient_checkbox.setEnabled(True)
    def turn_off_tcr(self):
        print("TCR OFF")
        self.tcr = False
        self.ui.tcr_indicator.setText("TCR OFF")
        self.ui.tcr_indicator.setStyleSheet("color: red; font-weight: bold")
        self.ui.toggle_tcr_button.setText("Turn TCR on")
        self.ui.launch_control_checkbox.setEnabled(False)
        self.ui.forced_coefficient_checkbox.setEnabled(False)
    def change_drop_rate(self):
        try:
            new_drop_rate_value = float(self.ui.drop_rate_input.text())
            self.drop_rate_value = new_drop_rate_value
            self.ui.drop_rate_input.setText(str(new_drop_rate_value))
            self.ui.current_drop_rate.setText(f"Current: {str(new_drop_rate_value)}")
            config['tcr_drop_rate'] = str(new_drop_rate_value)
            write_config(config)
        except ValueError:
            print("Invalid multiplier! Please enter a number.")
            self.show_warning("Invalid multiplier! Please enter a number.")

    def change_threshold(self):
        try:
            new_threshold_value = float(self.ui.threshold_input.text())
            self.threshold_value = new_threshold_value
            self.ui.threshold_input.setText(str(new_threshold_value))
            self.ui.current_threshold.setText(f"Current: {str(new_threshold_value)}")
            config['tcr_threshold'] = str(new_threshold_value)
            write_config(config)
        except ValueError:
            print("Invalid threshold! Please enter a number.")
            self.show_warning("Invalid threshold! Please enter a number.")
    def change_minimum_coefficient(self):
        try:
            new_minimum_coefficient = float(self.ui.minimum_coefficient_input.text())
            self.minimum_coefficicient_value = new_minimum_coefficient
            self.ui.minimum_coefficient_input.setText(str(new_minimum_coefficient))
            self.ui.current_minimum_coefficient.setText(f"Current: {str(new_minimum_coefficient)}")
            config['tcr_minimum_coefficient'] = str(new_minimum_coefficient)
            write_config(config)
        except ValueError:
            print("Invalid minimum coefficient! Please enter a number.")
            self.show_warning("Invalid minimum coefficient! Please enter a number.")
    def toggle_forced_coefficient(self, state):
        enabled = state == QtCore.Qt.Checked
        print(enabled)
        self.tcr_forced = enabled
        self.ui.forced_coefficient_input.setEnabled(enabled)
        self.ui.forced_coefficient_change.setEnabled(enabled)

    def toggle_launch_control(self, state):
        enabled = state == QtCore.Qt.Checked
        print(enabled)
        self.lc = enabled
        # print(self.lc)


    def change_forced_coefficient(self):
        try:
            new_forced_coeffecient = float(self.ui.forced_coefficient_input.text())
            self.forced_coefficient_value = new_forced_coeffecient
            self.ui.forced_coefficient_input.setText(str(new_forced_coeffecient))
        except ValueError:
            print("Invalid forced coefficient! Please enter a number.")
            self.show_warning("Invalid forced coefficient! Please enter a number.")

    def show_warning(self, message):
        """Display a warning message box."""
        warning = QMessageBox()
        warning.setWindowTitle("Error")
        warning.setText(message)
        warning.exec_()

if __name__ == "__main__":
    pygame.init()
    try:
        from resources import config, write_config
        # Create a queue for inter-process communication
        telemetry_queue = Queue() # queue to get telemetry from the listener
        controller_modifier_queue = Queue() # queue to sent data for controller modifier
        speed_queue = Queue() # queue to send speed to the acceleration calculator
        acceleration_time_queue = Queue() # queue to get acceleration times
        toggle_tcr_queue = Queue() # queue to get signals from input device to turn on/off TCR

        # Start the PyQt5 application
        app = QApplication(sys.argv)
        window = MainWindow(telemetry_queue, controller_modifier_queue, toggle_tcr_queue, acceleration_time_queue)
        window.show()
        # Run the event loop
        sys.exit(app.exec_())
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        window.disable_virtual_controller()
        window.stop_listening_telemetry()
