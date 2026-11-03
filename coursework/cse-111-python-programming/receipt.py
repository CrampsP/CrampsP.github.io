import csv
from datetime import datetime


def main():
    print("Inkom Emporium")
    products_dict = read_products("products.csv")
    if products_dict is None:
        return  

    process_requests("request.csv", products_dict)

def read_products(filename):
    products = {}
    try:
        with open(filename, "r") as product_file:
            productsdict = csv.reader(product_file)
            next(productsdict)
            for i in productsdict:
                product_num = i[0]
                products[product_num] = i
        return products
    except FileNotFoundError as nofile:
        print("Error: missing file")
        print(nofile)
        return None


def process_requests(filename, products_dict):
    try:
        items = 0
        subtotal = 0.0

        print("\nRequested Items")

        with open(filename, "r") as request_file:
            request_dict = csv.reader(request_file)
            next(request_dict) 

            for row in request_dict:
                product_num = row[0]
                quantity = int(row[1])

                product = products_dict[product_num]
                name = product[1]
                price = float(product[2])

                items += quantity
                subtotal += price * quantity

                print(f"{name}: {quantity} @ {price:.2f}")

        tax = subtotal * 0.06
        total = subtotal + tax

        print(f"\nNumber of Items: {items}")
        print(f"Subtotal: {subtotal:.2f}")
        print(f"Sales Tax: {tax:.2f}")
        print(f"Total: {total:.2f}")

        print("\nThank you for shopping at the Inkom Emporium.")

        current_date_and_time = datetime.now()
        print(current_date_and_time.strftime("%a %b %d %H:%M:%S %Y"))

    except KeyError as e:
        print("Error: unknown product ID in the request.csv file")
        print(e)



if __name__ == "__main__":
    main()
