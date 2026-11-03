print(
'''This program is an implementation of the Rosenberg
Self-Esteem Scale. This program will show you ten
statements that you could possibly apply to yourself.
Please rate how much you agree with each of the
statements by responding with one of these four letters:
D means you strongly disagree with the statement.
d means you disagree with the statement.
a means you agree with the statement.
A means you strongly agree with the statement.'''
)

interview = ["I feel that I am a person of worth, at least on an equal plane with others.",
    "I feel that I have a number of good qualities.",
    "All in all, I am inclined to feel that I am a failure.",
    "I am able to do things as well as most other people.",
    "I feel I do not have much to be proud of.",
    "I take a positive attitude toward myself.",
    "On the whole, I am satisfied with myself.",
    "I wish I could have more respect for myself.",
    "I certainly feel useless at times.",
    "At times I think I am no good at all."]


def questions():
    answers = []  # Create a list to store answers
    for i in interview:
        answer = input(i + " ")
        answers.append(answer)  # Add each answer to the list
    return answers


# Positive statements: D=0, d=1, a=2, A=3
positive_key = {"D": 0, "d": 1, "a": 2, "A": 3}
# Negative statements (reversed): D=3, d=2, a=1, A=0
negative_key = {"D": 3, "d": 2, "a": 1, "A": 0}

# Get all answers
all_answers = questions()

# Calculate scores
# Questions 1, 2, 4, 6, 7 are positive (indices 0, 1, 3, 5, 6)
# Questions 3, 5, 8, 9, 10 are negative/reversed (indices 2, 4, 7, 8, 9)
total_score = 0
for index, answer in enumerate(all_answers):
    if index in [2, 4, 7, 8, 9]:  # Negative questions
        score = negative_key.get(answer, 0)
    else:  # Positive questions
        score = positive_key.get(answer, 0)
    total_score += score

print(f"Your score is: {total_score}")
print("A score below 15 may indicate problematic low self-esteem.")