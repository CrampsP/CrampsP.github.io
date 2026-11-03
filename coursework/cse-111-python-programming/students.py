def main():

    ans = input("Enter your I-Number: ")

    student = read_dictionary("students.csv")
    
    if ans in student:
        print(student[ans])
    else:
        print("No such student")

    return


def read_dictionary(filename):
    """Read the contents of a CSV file into a
    dictionary and return the dictionary.

    Parameters
        filename: the name of the CSV file to read.
    Return: a dictionary that contains
        the contents of the CSV file.
    """
    student = dict()

    with open(filename, "rt") as file:
        next(file)
        for i in file:
            number = i.split(",")
            student[number[0]] = number[1]
    return student

if __name__ == "__main__":
    main()