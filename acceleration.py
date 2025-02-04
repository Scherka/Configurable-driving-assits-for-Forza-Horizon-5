import time
from multiprocessing import Process, Queue

previous_speed = 0
speed = 0

class accelerationTimeCalculator():
    def __init__(self, input_queue, output_queue):
        self.previous_speed = 0
        self.speed = 0
        self.is_measuring = False
        self.input_queue = input_queue # Queue for current speed
        self.output_queue = output_queue # Queue for acceleration times output
        self.start_time = -1
        self.time100 = -1 # time to reach 100 km/h
        self.time200 = -1 # time to reach 200 km/h
        self.time300 = -1 # time to reach 300 km/h
        self.time400 = -1 # time to reach 400 km/h
        self.time500 = -1 # time to reach 500 km/h

    # Start measuring acceleration time
    def start(self):
        print("Started")
        self.start_time = time.time()
        self.is_measuring = True

    # Stop measuring acceleration time
    def stop(self):
        print("Stopped")
        self.start_time = -1
        self.time100 = -1
        self.time200 = -1
        self.time300 = -1
        self.time400 = -1
        self.time500 = -1
        self.is_measuring = False

    # Calculate acceleration time
    def calculate(self):
        while True:
            if not self.input_queue.empty():
                self.speed = abs(self.input_queue.get())*3.6 # m/s to km/h
            if self.is_measuring:
                if self.speed > 100 and self.time100 == -1:
                    self.time100 = time.time() - self.start_time
                    self.output_queue.put((self.time100, "100"))
                elif self.speed > 200 and self.time200 == -1:
                    self.time200 = time.time() - self.start_time
                    self.output_queue.put((self.time200, "200"))
                elif self.speed > 300 and self.time300 == -1:
                    self.time300 = time.time() - self.start_time
                    self.output_queue.put((self.time300, "300"))
                elif self.speed > 400 and self.time400 == -1:
                    self.time400 = time.time() - self.start_time
                    self.output_queue.put((self.time400, "400"))
                elif self.speed > 500 and self.time500 == -1:
                    self.time500 = time.time() - self.start_time
                    self.output_queue.put((self.time500, "500"))
                elif self.speed < 0.01:
                    self.stop() # Stop measuring time if player stops
                    print("Stopped")
            elif self.previous_speed < 0.01 and self.speed > 0.01:
                self.start() # Start measuring time when player starts moving
            self.previous_speed = self.speed
            time.sleep(0.01)

# Create acceleration time calculator
def calculate_acceleration_time(input_queue, output_queue):
    calculator = accelerationTimeCalculator(input_queue, output_queue)
    calculator.calculate()