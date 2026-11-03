# discount

# Import the datetime class from the datetime
# module so that it can be used in this program.
from datetime import datetime

# Call the now() method to get the current
# date and time as a datetime object from
# the computer's operating system.
current_date_and_time = datetime.now()


# Call the weekday() method to get the day of the
# week from the current_date_and_time object.
day_of_week = current_date_and_time.weekday()

#day_of_week = int(input("What day is it:
# Monday = 0,
# Tuesday = 1,
# Wedesday = 2,
# Thursday = 3,
# Friday = 4,
# Saturday = 5,
# Sunday 6
# : "))

sub = float(input("Please enter the subtotal: "))

if day_of_week in (1,2):
    discount = float(sub * 0.1)
else: 
    discount = 0

if sub >= 50:
    apply = (sub - discount)
else:
    apply = sub
tax = (apply * 0.06)
total = apply + tax

if discount != 0:
    print(f"Discount amount: {discount}")
print(f"Sales tax amount: {tax}")
print(f"Total: {total}")