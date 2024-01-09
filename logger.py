from datetime import datetime

# gets the file name based on the date
def get_file_name():
    current_datetime = datetime.now()
    current_date = current_datetime.date()
    filename = "log_files/" + str(current_date) + ".txt"
    return filename


# if an error occurs, this will record the error
def write_for_error(error_str):
    print("Error occurred:", error_str)

    try:
        file_name = get_file_name()

        with open(file_name, 'a') as file:
            file.write(str(error_str) + '\n')

    except Exception as e:
        print(f"An error occurred while writing to the file: {e}")


# for the simulation, if the game completes this will add to the file
def write_for_successful_run(str):
    print("Success")

    f = get_file_name()
    with open(f, 'a') as file:
        file.write(str + "\n")

    file.close()


# writes the average numbver of moves based on how many iterationg of the simulation
def write_average_move_sim(str):
    f = get_file_name()
    with open(f, 'a') as file:
        file.write(str + "\n")
    file.close()



# Get the current date and time
current_datetime = datetime.now()

# Extract the date part
current_date = current_datetime.date()

# Print the current date
print("Current Date:", current_date)
