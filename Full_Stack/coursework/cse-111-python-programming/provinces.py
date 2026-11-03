      
def main():
    province_list = read("provinces.txt")

    print(province_list)

def read(filename):
    new_list = []

    with open(filename, mode = "rt") as file:

        for line in file:
            new_list.append(line)
    return new_list

if __name__ == "__main__":
    main()