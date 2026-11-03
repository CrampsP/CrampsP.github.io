# tire_volume

# Import the datetime class from the datetime
# module so that it can be used in this program.
from datetime import datetime

# Call the now() method to get the current
# date and time as a datetime object from
# the computer's operating system.
current_date_and_time = datetime.now()

# Use an f-string to print only the date
# part of the current date and time.
print(f"{current_date_and_time:%Y-%m-%d}")

import math



pi = (math.pi) 
w = int(input("Enter the width of the tire in mm (ex 205): "))
a = int(input("Enter the aspect ratio of the tire (ex 60): "))
d = int(input("Enter the diameter of the wheel in inches (ex 15): "))
v = pi * (w**2) * a * (w * a + 2540 * d)/10000000000

print(f"The approximate volume is {v:.2f} liters")

with open("volumes.txt", "at") as volume_file:
    print(f"{current_date_and_time}, {w}, {a}, {d}, {v:.2f}", file=volume_file)