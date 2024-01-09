import mysql.connector
from mysql.connector import Error
import hashlib

def connect_to_db():
    try:
        conn = mysql.connector.connect(
            host='localhost',  # The public IP address of VM
            user='root',  # The username
            password='12345',  # The password
            database='checkmate',  # The database name specified
            port=33306  # The port you exposed in your Docker Compose file
        )
        return conn
    except Error as e:
        print("Error while connecting to MySQL", e)
        return None

def signup(username, email, password):
    conn = connect_to_db()
    if conn is not None and conn.is_connected():
        try:
            cursor = conn.cursor()
            # Check if email already exists
            cursor.execute("SELECT email FROM User WHERE email = %s;", (email,))
            if cursor.fetchone():
                print("Email already in use.")
                return False

            # Insert new user
            cursor.execute("INSERT INTO User (username, email, password) VALUES (%s, %s, %s);",
                           (username, email, password))
            user_id = cursor.lastrowid  # Get the newly created user's ID

            # Initialize statistics for the new user
            stats_insert_query = "INSERT INTO Statistic (wins, losses, ties, User_ID) VALUES (0, 0, 0, %s);"
            cursor.execute(stats_insert_query, (user_id,))

            conn.commit()
            print("Signup and statistic initialization successful.")
            return True
        except Error as e:
            print(f"Error during signup: {e}")
            conn.rollback()  # Roll back in case of error
        finally:
            cursor.close()
            conn.close()


def login(email, password):
    conn = connect_to_db()
    if conn is not None and conn.is_connected():
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT User_ID, password FROM User WHERE email = %s;", (email,))
            result = cursor.fetchone()
            if result:
                db_password = str(result[1])
                input_password = str(password)
                print(f"Debug: Fetched password from database: {db_password}, Type: {type(db_password)}")
                print(f"Debug: Password provided for login: {input_password}, Type: {type(input_password)}")
                if db_password == input_password:
                    user_id = result[0]
                    user_data = get_user_data(user_id)
                    print("Login successful")
                    return user_id, user_data
                else:
                    print("Invalid login credentials.")
                    return None, None
            else:
                print("Email not found.")
                return None, None  # Return None for both values
        except Error as e:
            print(f"Error: {e}")
        finally:
            cursor.close()
            conn.close()



def get_user_data(user_id):
    conn = connect_to_db()
    if conn is not None and conn.is_connected():
        try:
            cursor = conn.cursor()
            # Get game data
            cursor.execute("SELECT * FROM Game WHERE User_ID = %s;", (user_id,))
            games = cursor.fetchall()
            # Get statistics data
            cursor.execute("SELECT * FROM Statistic WHERE User_ID = %s;", (user_id,))
            statistics = cursor.fetchall()
            return {"games": games, "statistics": statistics}
        except Error as e:
            print(f"Error: {e}")
        finally:
            cursor.close()
            conn.close()

def change_username(user_id, new_username):
    conn = connect_to_db()
    cursor = conn.cursor()
    try:
        query = "UPDATE users SET username = %s WHERE id = %s"
        cursor.execute(query, (new_username, user_id))
        conn.commit()
    except Error as e:
        print(f"Error updating username: {e}")
    finally:
        cursor.close()
        conn.close()

def change_password(user_id, new_password):
    conn = connect_to_db()
    cursor = conn.cursor()
    hashed_password = hashlib.sha256(new_password.encode()).hexdigest()
    try:
        query = "UPDATE users SET password = %s WHERE id = %s"
        cursor.execute(query, (hashed_password, user_id))
        conn.commit()
    except Error as e:
        print(f"Error updating password: {e}")
    finally:
        cursor.close()
        conn.close()

def delete_account(user_id):
    conn = connect_to_db()
    cursor = conn.cursor()
    try:
        query = "DELETE FROM users WHERE id = %s"
        cursor.execute(query, (user_id,))
        conn.commit()
    except Error as e:
        print(f"Error deleting account: {e}")
    finally:
        cursor.close()
        conn.close()

def save_game_outcome(user_id, outcome):
    conn = connect_to_db()
    if conn is not None and conn.is_connected():
        try:
            cursor = conn.cursor()
            # Assuming there is a 'Statistics' table with columns 'wins', 'losses', 'ties', and 'User_ID'
            update_stat_query = ""
            print(f"Updating outcome with: {outcome}")
            if outcome == 'win':
                update_stat_query = "UPDATE Statistic SET wins = wins + 1 WHERE User_ID = %s;"
            elif outcome == 'loss':
                update_stat_query = "UPDATE Statistic SET losses = losses + 1 WHERE User_ID = %s;"
            elif outcome == 'tie':
                update_stat_query = "UPDATE Statistic SET ties = ties + 1 WHERE User_ID = %s;"

            cursor.execute(update_stat_query, (user_id,))
            conn.commit()
        except Error as e:
            print(f"Error: {e}")
        finally:
            if cursor is not None:
                cursor.close()
            if conn is not None:
                conn.close()

def retrieve_player_stats_and_games(user_id):
    conn = connect_to_db()
    if conn is not None and conn.is_connected():
        try:
            cursor = conn.cursor()
            # Retrieve statistics
            stats_query = "SELECT wins, losses, ties FROM Statistic WHERE User_ID = %s;"
            cursor.execute(stats_query, (user_id,))
            stats = cursor.fetchone()

            # Retrieve games
            games_query = "SELECT Game_ID, outcome, date_played FROM Game WHERE User_ID = %s;"
            cursor.execute(games_query, (user_id,))
            games = cursor.fetchall()

            return {"statistics": stats, "games": games}
        except Error as e:
            print(f"Error: {e}")
        finally:
            cursor.close()
            conn.close()


