def factorial(n):
    if n == 0:
        return 1
    else:
        return n * factorial(n - 1)

# Input a number for which you want to calculate the factorial
number = int(input("Enter a number:1 "))
