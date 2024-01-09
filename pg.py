import sys, engine

import chess
import pygame
from pygame.locals import *
import time
import db
# comment for test push
# Initialize pygame
pygame.init()

# Setting up the display window
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Checkmate Chess")

# Colors
BACKGROUND_COLOR = (254, 255, 224)
BLACK = (0, 0, 0)
BUTTON_COLOR = (190, 252, 89)
WHITE = (255, 255, 255)
BLUE = (0, 128, 255)
RED = (255, 0, 0)
BOARDWIDTH = 9

# image size
GRID_SIZE = 8
SQUARE_SIZE = 30

USER = None

class User:
    def __init__(self, user_id, username, email, wins=0, losses=0, ties=0, games=None):
        self.user_id = user_id
        self.username = username
        self.email = email
        self.wins = wins
        self.losses = losses
        self.ties = ties
        self.games = games or []

    def update_statistics(self, statistics_data):
        self.wins = statistics_data['wins']
        self.losses = statistics_data['losses']
        self.ties = statistics_data['ties']

    def add_game(self, game_data):
        self.games.append(game_data)



# Button class to create and manage button elements
class Button:
    def __init__(self, color, x, y, width, height, text=''):
        self.color = color
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.text = text

    # Draws the button on the screen.
    def draw(self, screen, text_color=BLACK, font_size=30):
        pygame.draw.rect(screen, self.color, (self.x, self.y, self.width, self.height))
        if self.text != '':
            font = pygame.font.SysFont('comicsans', font_size)
            text = font.render(self.text, 1, text_color)
            screen.blit(text, (self.x + (self.width // 2 - text.get_width() // 2),
                               self.y + (self.height // 2 - text.get_height() // 2)))

    # Method to check if a point (like mouse click) is over the button
    def is_over(self, pos):
        if self.x < pos[0] < self.x + self.width:
            if self.y < pos[1] < self.y + self.height:
                return True
        return False


# InputBox class for creating text input fields
class InputBox:
    def __init__(self, x, y, w, h, text='', hint='', password=False):
        self.rect = pygame.Rect(x, y, w, h)
        self.ispassword = password
        self.password = ''
        self.color_inactive = pygame.Color('lightskyblue3')
        self.color_active = pygame.Color('dodgerblue2')
        self.color = self.color_inactive
        self.text = text
        self.txt_surface = pygame.freetype.SysFont('comicsans', 20).render(text)[0]
        self.active = False
        self.hint = hint
        self.hint_color = pygame.Color('grey')

    # Method to handle input and color changes on activation
    def handle_event(self, event):
        # Check if the event is a mouse button press
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Check if the mouse click occurred within the input box's rectangle
            if self.rect.collidepoint(event.pos):
                # Toggle the active state of the input box
                self.active = not self.active
            else:
                # If the click was outside the box, deactivate the box
                self.active = False
            # Set the input box's color based on its active state
            self.color = self.color_active if self.active else self.color_inactive

        # Check if the event is a key press while the input box is active
        if event.type == pygame.KEYDOWN:
            if self.active:
                # Check if the 'Enter' key was pressed
                if event.key == pygame.K_RETURN:
                    pass
                # Check if the 'Backspace' key was pressed
                elif event.key == pygame.K_BACKSPACE:
                    # Remove the last character from the input box's text
                    self.text = self.text[:-1]
                    self.password = self.password[:-1]
                elif self.ispassword:
                    # if we are entering input for password we will conceal it with dots
                    self.password += event.unicode
                    self.text += u"\u0387"
                else:
                    # Add the pressed key's character to the input box's text
                    self.text += event.unicode

                # Re-render the text to update the display
                self.txt_surface = pygame.freetype.SysFont('K2D', 20).render(self.text)[0]
                # Check if the text's width exceeds the input box's width
                if self.txt_surface.get_width() > self.rect.w:
                    # If it does, remove the last character to prevent overflow
                    self.text = self.text[:-1]

    # Method to draw the input box on screen
    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect, 2)
        if not self.text:
            hint_surface, _ = pygame.freetype.SysFont('K2D', 20).render(self.hint, self.hint_color)
            screen.blit(hint_surface, (self.rect.x + 10, self.rect.y + self.rect.h // 4))
        else:
            screen.blit(self.txt_surface, (self.rect.x + 10, self.rect.y + self.rect.h // 4))


# The main class that manages the game application states and logic
class CheckmateEngine:
    def __init__(self):
        self.timer_time = 20
        self.current_page = 'start'
        blue_color = (0, 128, 255)
        red_color = (255, 0, 0)
        self.username_input = InputBox(250, 350, 300, 40, hint='Username')
        self.password_input = InputBox(250, 300, 300, 40, hint='Password', password=True)
        self.email_input = InputBox(250, 250, 300, 40, hint='Email')
        self.move_input = InputBox(WIDTH // 2 - 90, 450, 200, 40, hint='Enter Move')
        self.timer_input = InputBox(WIDTH // 2 + 150, HEIGHT // 2 - 100, 120, 40, hint='20')
        self.input_boxes = [self.email_input, self.password_input]
        self.registration_input_boxes = [self.username_input, self.password_input, self.email_input]

        # used for pvp page
        self.player1_input = InputBox(WIDTH // 2 - 90, 450, 200, 40, hint='Enter Move')
        self.player2_input = InputBox(WIDTH // 2 - 90, 500, 200, 40, hint='Enter Move')
        self.player1_moves = []  # Stores the moves made by player 1
        self.player2_moves = []  # Stores the moves made by player 2
        self.current_player = 1  # Start with player 1
        self.board = [['.' for _ in range(BOARDWIDTH)] for _ in range(BOARDWIDTH)]

        self.user_id = None

        # For username update
        self.new_username_input = InputBox(250, 200, 300, 40, hint='New Username')
        self.confirm_username_input = InputBox(250, 250, 300, 40, hint='Confirm Username')
        # For password update
        self.new_password_input = InputBox(250, 200, 300, 40, hint='New Password')
        self.confirm_password_input = InputBox(250, 250, 300, 40, hint='Confirm Password')

        # List to store past moves
        self.user_past_moves = []
        self.engine_past_moves = []
        # for countdown timer
        self.remaining_time = 20 * 60  # 20 minutes in seconds
        self.timer_started = False
        self.game_start_time = None
        self.incorrect_password = False

        # Draws the starting page of the game
    def draw_start_page(self):
        # Fill the screen with the background color to clear the previous frame
        screen.fill(BACKGROUND_COLOR)
        font = pygame.font.SysFont('comicsans', 80, bold=True)
        text = font.render('Checkmate', True, BLACK)
        # Get a rectangle object for the text, centered on the screen and offset upwards by 50 pixels
        text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 50))
        # Draw the text onto the screen at the position defined by text_rect
        screen.blit(text, text_rect)
        start_btn = Button(BUTTON_COLOR, WIDTH // 2 - 70, HEIGHT // 2 + 40, 140, 40, 'Start')
        start_btn.draw(screen)
        # Return the start button object for further use, such as detecting clicks
        return start_btn

    # Draws the login page of the game
    def draw_login_page(self):
        # Clears the screen by filling it with a background color.
        screen.fill(BACKGROUND_COLOR)
        font = pygame.font.SysFont('comicsans', 45, bold=True)
        text = font.render('Checkmate', True, BLACK)
        # Gets a rectangle object that encapsulates the text, positioned at the center of the screen
        # width-wise and 50 pixels from the top.
        text_rect = text.get_rect(center=(WIDTH // 2, 50))
        info_font = pygame.font.SysFont('comicsans', 12, bold=True)
        info_text = info_font.render('Incorrect Username/Password', True, (255, 0, 0))
        # width-wise and 20 pixels from the bottom.
        info_rect = info_text.get_rect(center=(WIDTH // 2, HEIGHT - 20))
        if self.incorrect_password:
            screen.blit(info_text, info_rect)
        # Draws the 'Checkmate' text onto the screen at the position defined by text_rect.
        screen.blit(text, text_rect)
        # Draws the username and password input boxes on the screen.
        go_btn = Button(BUTTON_COLOR, WIDTH // 2 - 60, HEIGHT // 2 + 80, 120, 50, 'Log in')
        sign_up_btn = Button(BUTTON_COLOR, WIDTH // 2 - 60, HEIGHT // 2 + 140, 120, 50, 'Sign up')
        go_btn.draw(screen)
        sign_up_btn.draw(screen)
        # # Iterates over each input box (username and password) and draws them on the screen.
        for box in self.input_boxes:
            box.draw(screen)
        return go_btn, sign_up_btn
    # Draws the login page of the game
    def draw_registration_page(self):
        # Clears the screen by filling it with a background color.
        screen.fill(BACKGROUND_COLOR)
        font = pygame.font.SysFont('comicsans', 45, bold=True)
        text = font.render('Checkmate', True, BLACK)
        # Gets a rectangle object that encapsulates the text, positioned at the center of the screen
        # width-wise and 50 pixels from the top.
        text_rect = text.get_rect(center=(WIDTH // 2, 50))
        # Draws the 'Checkmate' text onto the screen at the position defined by text_rect.
        screen.blit(text, text_rect)
        # Draws the username and password input boxes on the screen.
        # Back login button on top right
        back_log_btn = Button(WHITE, WIDTH - 70, 10, 60, 30, 'Back')
        back_log_btn.draw(screen, BLACK, 20)
        # Register button creation in the middle below the email box
        register_btn = Button(BUTTON_COLOR, WIDTH // 2 - 60, HEIGHT // 2 + 130, 130, 50, 'Register')
        register_btn.draw(screen)
        # Iterates over each input box (username, password, email) and draws them on the screen.
        for box in self.registration_input_boxes:
            box.draw(screen)
        return register_btn, back_log_btn

    # Draws the main home page of the game with different engine options
    def draw_home_page(self):
        screen.fill(BACKGROUND_COLOR)

        # Displaying Checkmate title
        font_title = pygame.font.SysFont('comicsans', 45, bold=True)
        text = font_title.render('Checkmate', True, BLACK)
        text_rect = text.get_rect(center=(WIDTH // 2, 50))
        screen.blit(text, text_rect)

        # Back login button on top right
        back_log_btn = Button(BLACK, WIDTH - 110, 10, 100, 40, 'Log Out')
        font_back = pygame.font.SysFont('comicsans', 20)
        back_text = font_back.render('Log Out', True, BLACK)
        back_rect = back_text.get_rect(center=(WIDTH - 60, 25))
        screen.blit(back_text, back_rect)

        # Buttons under Checkmate title
        new_game_btn = Button(BUTTON_COLOR, WIDTH // 2 - 110, HEIGHT // 2 - 100, 250, 40, 'New Game')
        pvp_btn = Button(BUTTON_COLOR, WIDTH // 2 - 110, HEIGHT // 2, 250, 40, 'Play with Friends')
        matching_history_btn = Button(BUTTON_COLOR, WIDTH // 2 - 110, HEIGHT // 2+ 100, 250, 40, 'Match History')
        account_btn = Button(BUTTON_COLOR, WIDTH // 2 - 110, HEIGHT // 2 + 200, 250, 40, 'Account')

        new_game_btn.draw(screen)
        pvp_btn.draw(screen)
        matching_history_btn.draw(screen)
        account_btn.draw(screen)

        # drawing timer input box and text
        timer_font = pygame.font.SysFont('comicsans', 14, bold=True)
        timer_text = timer_font.render('Match Minutes:', True, BLACK)
        timer_rect = timer_text.get_rect(center=(WIDTH // 2 + 200, HEIGHT // 2 - 120))
        screen.blit(timer_text, timer_rect)
        self.timer_input.draw(screen)

        return back_log_btn, new_game_btn, matching_history_btn, account_btn, pvp_btn
        # Returning the buttons so they can be accessed outside the method

    # Method to draw the back button on top-right
    def draw_back_button(self):
        # Initialize button with properties: color, position, dimensions, and label
        back_btn = Button(WHITE, WIDTH - 70, 10, 60, 30, 'Back')
        font_back = pygame.font.SysFont('comicsans', 20)

        # Render text and get its rectangle for positioning
        back_text = font_back.render('Back', True, BLACK)
        back_rect = back_text.get_rect(center=(WIDTH - 40, 25))

        # Display the text on the screen
        screen.blit(back_text, back_rect)
        return back_btn

    # Similar methods for drawing account, matching history, and new game page buttons
    # Each of these pages contains a Home button to navigate back to the main page
    def draw_account_page(self):
        screen.fill(BACKGROUND_COLOR)

        # Displaying title
        font_title = pygame.font.SysFont('comicsans', 45, bold=True)
        text = font_title.render('Account', True, BLACK)
        text_rect = text.get_rect(center=(WIDTH // 2, 50))
        screen.blit(text, text_rect)
        # home button
        home_btn = Button(WHITE, WIDTH - 100, 10, 80, 30, 'Home')
        home_btn.draw(screen, text_color=BLACK, font_size=20)

        # Create buttons for account page
        change_username_btn = Button(BUTTON_COLOR, WIDTH // 2 - 150, 150, 300, 50, 'Change Username')
        change_password_btn = Button(BUTTON_COLOR, WIDTH // 2 - 150, 250, 300, 50, 'Change Password')
        delete_account_btn = Button(BUTTON_COLOR, WIDTH // 2 - 150, 350, 300, 50, 'Delete Account')

        # Drawing buttons on the screen
        change_username_btn.draw(screen)
        change_password_btn.draw(screen)
        delete_account_btn.draw(screen)

        return home_btn, change_username_btn, change_password_btn, delete_account_btn

    def draw_info_edit_username_page(self):
        screen.fill(BACKGROUND_COLOR)

        # Displaying title: "Username Update"
        # The title is centered at the top of the screen.
        font_title = pygame.font.SysFont('comicsans', 45, bold=True)
        text = font_title.render('Username Update', True, BLACK)
        text_rect = text.get_rect(center=(WIDTH // 2, 50))
        screen.blit(text, text_rect)

        # Drawing input fields for new username and confirmation
        self.new_username_input.draw(screen)
        self.confirm_username_input.draw(screen)

        # Creating 'Back' and 'Submit' buttons for navigation and action
        back_acc_btn = Button(BUTTON_COLOR, WIDTH // 2 - 160, 300, 100, 50, 'Back')
        back_acc_btn.draw(screen)
        submit_acc_btn = Button(BUTTON_COLOR, WIDTH // 2 + 60, 300, 100, 50, 'Submit')
        submit_acc_btn.draw(screen)
        # Return the button objects for further interaction handling
        return submit_acc_btn, back_acc_btn

    def draw_info_edit_password_page(self):
        screen.fill(BACKGROUND_COLOR)

        # Displaying title: "Password Update"
        # The title is centered at the top of the screen.
        font_title = pygame.font.SysFont('comicsans', 45, bold=True)
        text = font_title.render('Password Update', True, BLACK)
        text_rect = text.get_rect(center=(WIDTH // 2, 50))
        screen.blit(text, text_rect)

        # Drawing input fields for new password and confirmation
        self.new_password_input.draw(screen)
        self.confirm_password_input.draw(screen)

        # Creating 'Back' and 'Submit' buttons for navigation and action
        back_acc_btn = Button(BUTTON_COLOR, WIDTH // 2 - 160, 300, 100, 50, 'Back')
        back_acc_btn.draw(screen)
        submit_acc_btn = Button(BUTTON_COLOR, WIDTH // 2 + 60, 300, 100, 50, 'Submit')
        submit_acc_btn.draw(screen)
        # Return the button objects for further interaction handling
        return submit_acc_btn, back_acc_btn

    def on_submit_username_click(self):
        if self.new_username_input.text == self.confirm_username_input.text:
            if self.user_id is not None:
                db.change_username(self.user_id, self.new_username_input.text)
                print(f"Username be changed to {self.new_username_input.text}")
            else:
                print("User ID is not set. Please log in first.")
        else:
            print("Input check doesn't match")

    def on_submit_password_click(self):
        if self.new_password_input.password == self.confirm_password_input.password:
            if self.user_id is not None:
                db.change_password(self.user_id, self.new_password_input.password)
                print(f"Username be changed to {self.new_password_input.password}")
            else:
                print("User ID is not set. Please log in first.")
        else:
            print("Input check doesn't match")
    def on_delete_account_click(self):
        # Delete account function in db.py
        db.delete_account(self.user_id)

    def draw_matching_history_page(self):
        screen.fill(BACKGROUND_COLOR)

        # Displaying title
        font_title = pygame.font.SysFont('comicsans', 45, bold=True)
        text = font_title.render('Match History', True, BLACK)
        text_rect = text.get_rect(center=(WIDTH // 2, 50))
        text = font_title.render(f'Wins:{USER.wins} Ties:{USER.ties} Losses:{USER.losses}', True, BLACK)
        

        screen.blit(text, text_rect)
        # home button
        home_btn = Button(WHITE, WIDTH - 100, 10, 80, 30, 'Home')
        home_btn.draw(screen, text_color=BLACK, font_size=20)   
        return home_btn

    """
    def start_player_turn(self):
        if not self.first_move_made:  # Start the timer on the first move
            self.last_move_time = time.time()
            self.first_move_made = True
            

    def end_player_turn(self):
        if self.first_move_made and self.last_move_time:
            time_spent = time.time() - self.last_move_time
            self.remaining_time -= time_spent
            self.last_move_time = None  # Reset the timer for the engine's turn
            
    def update_timer(self):
        if self.first_move_made and self.last_move_time:
            time_spent = time.time() - self.last_move_time
            self.remaining_time -= time_spent
            self.last_move_time = time.time()
            if self.remaining_time <= 0:
                self.remaining_time = 0
    """

    def draw_pvp_page(self):
        screen.fill(BACKGROUND_COLOR)

        # Displaying title
        font_title = pygame.font.SysFont('comicsans', 45, bold=True)
        text = font_title.render('Player VS Player', True, BLACK)
        text_rect = text.get_rect(center=(WIDTH // 2, 50))
        screen.blit(text, text_rect)

        # home button
        home_btn = Button(WHITE, WIDTH - 100, 10, 80, 30, 'Home')
        home_btn.draw(screen, text_color=BLACK, font_size=20)

        # Input boxes for both players
        self.player1_input.draw(screen)
        self.player2_input.draw(screen)
        enter_btn_1 = Button(BLUE, WIDTH // 2 + 150, 455, 80, 30, 'Enter')
        enter_btn_1.draw(screen, text_color=BLACK, font_size=20)
        enter_btn_2 = Button(RED, WIDTH // 2 + 150, 505, 80, 30, 'Enter')
        enter_btn_2.draw(screen, text_color=BLACK, font_size=20)

        mess_font = pygame.font.SysFont('comicsans', 14, bold=False)
        self.get_legal_moves()  # gets the current legal moves for the player
        self.build_board # builds the current board
        message = mess_font.render(engine.message, True, BLACK)  # shows message from the engine
        mess_rect = message.get_rect(center=(100, HEIGHT - 20))
        screen.blit(message, mess_rect)
        self.move_input.draw(screen)

        return home_btn, enter_btn_1, enter_btn_2


    def draw_past_moves(self):
        move_font = pygame.font.SysFont('comicsans', 20)
        title_font = pygame.font.SysFont('comicsans', 30, bold=True)
        ypos = 100  # Starting y position for displaying moves

        # Render and display the title for the past moves section
        title_surface = title_font.render('Past Moves', True, BLACK)
        screen.blit(title_surface, (WIDTH - 200, ypos))  # Adjust position as needed
        ypos = 140  # Adjust space after the title

        # Iterate through user past moves and display them
        user_past_moves = self.user_past_moves[-15:]
        engine_past_moves = self.engine_past_moves[-15:]
        for move in user_past_moves:
            move_surface = move_font.render(move, True, (173, 216, 230))  # Blue color for user moves
            screen.blit(move_surface, (WIDTH - 180, ypos))
            ypos += 30
        ypos = 140
        # Iterate through engine past moves and display them
        for move in engine_past_moves:
            move_surface = move_font.render(move, True, (255,114,118))  # Red color for engine moves
            screen.blit(move_surface, (WIDTH - 110, ypos))
            ypos += 30


    # display new game page
    def draw_new_game_page(self):
        home_btn = Button(WHITE, WIDTH - 100, 10, 80, 30, 'Home')
        home_btn.draw(screen, text_color=BLACK, font_size=20)
        title_font = pygame.font.SysFont('comicsans', 45, bold=True)
        mess_font = pygame.font.SysFont('comicsans', 14, bold=False)
        self.get_legal_moves()  # gets the current legal moves for the player
        title = title_font.render('Player Vs. Engine', True, BLACK)
        self.build_board()  # builds the current board
        message = mess_font.render(engine.message, True, BLACK) # shows message from the engine
        text_rect = title.get_rect(center=(WIDTH // 2, 50))
        mess_rect = message.get_rect(center=(100, HEIGHT - 20))
        screen.blit(title, text_rect)
        screen.blit(message, mess_rect)
        self.move_input.draw(screen)
        # displays the user input and enter buttons
        enter_btn = Button(WHITE, WIDTH // 2 - 30, 500, 80, 30, 'Enter')
        enter_btn.draw(screen, text_color=BLACK, font_size=20)


        # Draw the countdown timer
        # Start the timer only if it hasn't been started before
        if not self.timer_started:
            self.game_start_time = time.time()
            self.timer_started = True

        # Calculate the remaining time only if the timer has started
        if self.timer_started:
            current_time = time.time()
            elapsed_time = current_time - self.game_start_time
            self.remaining_time = max(0, self.timer_time - elapsed_time)
            if self.remaining_time == 0:
                self.current_page = 'times_up'
                self.draw_times_up_page()

        # Render the timer text
        minutes, seconds = divmod(int(self.remaining_time), 60)
        timer_text = f"{minutes:02d}:{seconds:02d}"
        timer_font = pygame.font.SysFont('comicsans', 30)
        timer_surface = timer_font.render(timer_text, True, BLACK)
        timer_rect = timer_surface.get_rect(topright=(WIDTH - 10, 60))
        screen.blit(timer_surface, timer_rect)

        # Draw the past moves list
        self.draw_past_moves()

        return home_btn, enter_btn

    # once the timer on the new game page runs out this method will show a times up message and a return to home button
    def draw_times_up_page(self):
        # draw home button to take you back to home page
        home_btn = Button(WHITE, WIDTH - 100, 10, 80, 30, 'Home')
        home_btn.draw(screen, text_color=BLACK, font_size=20)

        # draw times up text
        times_up_font = pygame.font.SysFont('comicsans', 60, bold=True)
        times_up_text = times_up_font.render('Times Up!', True, BLACK)
        times_up_rect = times_up_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        screen.blit(times_up_text, times_up_rect)

        return home_btn

    # obtains and displays the current legal moves for the player
    def get_legal_moves(self):
        move_font = pygame.font.SysFont('comicsans', 14, bold=False)
        legal_moves = []
        legal_moves_line = ""
        i = 0
        # obtain list of legal moves from engine
        for line in engine.legalMoves:
            i = i + 1
            legal_moves_line = legal_moves_line + line
            # create a string concatenating each move and creating a new line every 10 moves
            if i % 6 == 0:
                legal_moves.append(legal_moves_line)
                legal_moves_line = ""
        legal_moves.append(legal_moves_line)
        moves = [move_font.render("Move options: ", True, BLACK)]
        # run through each line of moves and make a list full of rendered fonts for each line
        for line in legal_moves:
            moves.append(move_font.render(line, True, BLACK))
        # display each line on screen
        for line in range(len(moves)):
            screen.blit(moves[line], (14, 100 + (line * 12) + (15 * line)))

    # builds the chess board on screen
    def build_board(self):
        board_font = pygame.font.Font('seguisym.ttf', 30)
        for row in range(BOARDWIDTH):
            for col in range(BOARDWIDTH):
                if engine.player_move is not None and ((engine.player_move[0] == str(col) and engine.player_move[1] == str(row)) or (engine.player_move[2] == str(col) and engine.player_move[3] == str(row))):
                    pygame.draw.rect(screen, (173, 216, 230), # draw blue square
                                     pygame.Rect((WIDTH // 2 - 140 + col * 30), 100 + row * 30, 30, 30))
                elif engine.enemy_move is not None and ((engine.enemy_move[0] == str(col) and engine.enemy_move[1] == str(row)) or (engine.enemy_move[2] == str(col) and engine.enemy_move[3] == str(row))):
                    pygame.draw.rect(screen, (255,114,118), # draw red square
                                     pygame.Rect((WIDTH // 2 - 140 + col * 30), 100 + row * 30, 30, 30))
                elif (row + col) % 2 == 1 or col == 0 or row == 8: # draw white square
                    pygame.draw.rect(screen, (255, 255, 255),
                             pygame.Rect((WIDTH // 2 - 140 + col * 30), 100 + row * 30, 30, 30))
                else: # draw grey square
                    pygame.draw.rect(screen, (211, 211, 211),
                                     pygame.Rect((WIDTH // 2 - 140 + col * 30), 100 + row * 30, 30, 30))
        board = []
        # run through printed board in engine and make new list with fonts for each line
        for line in engine.printedBoard:
            board.append(board_font.render(line, True, BLACK))
        # display each line of the board on screen
        for line in range(len(board)):
            screen.blit(board[line], ((WIDTH // 2 - 134), 94 + line * 30))

    def move_player(self):
        engine.player_turn(self.move_input.text)  # sends player info to engine
        # only if the user input is a valid move will it first draw the players move then
        # perform the enemy move
        if engine.valid_move:
            self.record_user_move(self.move_input.text)
            self.draw_new_game_page()
            engine.message = ""
            pygame.display.flip()

            # Get the engine's move and record it
            engine_move = engine.enemy_turn()
            self.record_engine_move(engine_move)

            # Check for game over after the engine move
            game_result = engine.check_game_over()
            if game_result['is_game_over']:
                self.current_page = 'home'  # Implement a game over page or functionality
                outcome = ''
                if game_result['winner'] == 'draw':
                    USER.ties += 1
                    outcome = 'tie'
                elif game_result['winner'] == 'white':
                    USER.wins += 1
                    outcome = 'win'

                else:
                    USER.losses += 1
                    outcome = 'loss'
                
                db.save_game_outcome(USER.user_id, outcome)
                
            else:
                # Update the display again if necessary
                self.draw_new_game_page()
                pygame.display.flip()

        self.move_input.text = ""
        
        # Call this method when a new game starts
    def start_new_game(self):
        # Set the end time for 20 minutes from now (1200 seconds)
        timer_time_string = ""
        self.timer_time = 20
        if len(self.timer_input.text) > 0:
            for char in self.timer_input.text.split():
                if char.isdigit():
                    timer_time_string = timer_time_string + char
        if len(timer_time_string) > 0:
            self.timer_time = int(timer_time_string)
        self.timer_time = self.timer_time * 60
        self.past_moves = []  # Reset the past moves list

    # Method to update the past moves list
    def update_past_moves(self, move):
        self.past_moves.append(move)

    def record_user_move(self, move):
        self.user_past_moves.append(move)

    def format_move(self, move):
        # Implement the actual formatting logic as needed.
        if len(move) == 4:
            return f"{move[0:2]} to {move[2:4]}"
        else:
            # Handle special cases like castling, promotions, etc.
            return move

    def record_engine_move(self, move):
        # No need to format if already in desired format
        # formatted_move = self.format_move(move)
        self.engine_past_moves.append(move)

    def on_login_click(self, email, pwd):
        global USER
        user_id, user_data = db.login(email, pwd)
        print(f"Debug: Email provided for login: {email}")
        if user_id is not None:
            print("Login successful.")

            # Assuming user_data contains a 'statistics' key with relevant data
            if 'statistics' in user_data and user_data['statistics']:
                stats = user_data['statistics'][0]
                # Assuming the order is wins, ties, losses
                wins = stats[1]  # Index 1 for wins
                ties = stats[2]  # Index 2 for ties
                losses = stats[3]  # Index 3 for losses

                # Fetch username from another source or modify the query to include it
                username = ... # Retrieve username appropriately

                self.current_user = User(user_id, username, email, wins, losses, ties)
                USER = self.current_user
                print(f"Wins: {wins}, loses: {losses}")
            else:
                print("No statistics available for this user.")
            return user_id, user_data, True

        else:
            print("Login failed. Invalid credentials or user does not exist.")
            # Handle login failure
            return None, None, False

    
    
    def on_signup_click(self, user, email, pwd):
        print(f"Signup button pressed with email {email}, user {user} and password {pwd}")
        db.signup(user, email, pwd)
    
    # Main method to run the game/application
    def run(self):
        # Initialize game clock
        clock = pygame.time.Clock()
        running = True
        go_btn = None
        # Main game loop
        while running:
            # Set background color
            screen.fill(BACKGROUND_COLOR)

            submit_acc_btn = None
            back_acc_btn = None
            change_username_btn = None
            change_password_btn = None
            delete_account_btn = None
            home_btn = None


            # draws each page and assigns to pages buttons given the name of the current page
            if self.current_page == 'start':
                start_btn = self.draw_start_page()
            elif self.current_page == 'login':
                go_btn, sign_up_btn = self.draw_login_page()
            elif self.current_page == 'home':
                back_log_btn, new_game_btn, matching_history_btn, account_btn, pvp_btn = self.draw_home_page()
            elif self.current_page == 'account':
                home_btn, change_username_btn, change_password_btn, delete_account_btn = self.draw_account_page()
            elif self.current_page == 'pvp':
                home_btn,enter_btn_1, enter_btn_2 = self.draw_pvp_page()
            elif self.current_page == 'matching_history':
                home_btn = self.draw_matching_history_page()
            elif self.current_page == 'new_game':
                home_btn, enter_btn = self.draw_new_game_page()
            elif self.current_page == 'registration':
                register_btn, back_log_btn = self.draw_registration_page()
            elif self.current_page == 'info_edit_username':
                submit_acc_btn, back_acc_btn = self.draw_info_edit_username_page()
            elif self.current_page == 'info_edit_password':
                submit_acc_btn, back_acc_btn = self.draw_info_edit_password_page()
            elif self.current_page == 'times_up':
                home_btn = self.draw_times_up_page()

            # Event handling loop
            for event in pygame.event.get():
                if event.type == QUIT:
                    running = False

                # Check for input box events
                for box in self.registration_input_boxes:
                    box.handle_event(event)

                # Check input box events in new game and home pages
                if self.current_page == 'new_game':
                    self.move_input.handle_event(event)
                if self.current_page == 'home':
                    self.timer_input.handle_event(event)

                # Check input box events in pvp pages
                if self.current_page == 'pvp':
                    self.player1_input.handle_event(event)
                    self.player2_input.handle_event(event)




                # Handle input box events for username and password update pages
                if self.current_page in ['info_edit_username', 'info_edit_password']:
                    self.new_username_input.handle_event(event)
                    self.confirm_username_input.handle_event(event)
                    self.new_password_input.handle_event(event)
                    self.confirm_password_input.handle_event(event)

                # Handle mouse click events
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = pygame.mouse.get_pos()
                    if self.current_page == 'start':
                        if start_btn.is_over(mouse_pos):
                            self.current_page = 'login'
                    elif self.current_page == 'login':
                        if go_btn and go_btn.is_over(mouse_pos):
                            self.user_id, user_data, login_result = self.on_login_click(self.email_input.text, self.password_input.password)
                            print(f"Login result: {login_result}")
                            if login_result:
                                self.current_page = 'home'
                            else:
                                self.incorrect_password = True
                        elif sign_up_btn and sign_up_btn.is_over(mouse_pos):
                            # if there is input in the username and password input boxes on the login
                            # page, erase them for better look
                            self.username_input.text = ""
                            self.password_input.text = ""
                            self.password_input.password = ""
                            self.current_page = 'registration'
                    elif self.current_page == 'home':
                        # Here we'll check for button clicks for 'New Game', 'Matching History', and 'Account'
                        if new_game_btn and new_game_btn.is_over(mouse_pos):
                            self.current_page = 'new_game'
                            engine.reset()
                            self.start_new_game()
                        elif pvp_btn and pvp_btn.is_over(mouse_pos):
                            self.current_page = 'pvp'
                        elif matching_history_btn and matching_history_btn.is_over(mouse_pos):
                            self.current_page = 'matching_history'
                        elif account_btn and account_btn.is_over(mouse_pos):
                            self.current_page = 'account'
                        elif back_log_btn and back_log_btn.is_over(mouse_pos):
                            self.current_page = 'login'
                            self.incorrect_password = False
                    elif self.current_page in 'pvp':
                        if home_btn and home_btn.is_over(mouse_pos):
                            self.current_page = 'home'
                            # Check if the enter buttons are clicked
                        elif enter_btn_1 and enter_btn_1.is_over(mouse_pos):
                            self.handle_enter_press(1)
                        elif enter_btn_2 and enter_btn_2.is_over(mouse_pos):
                            self.handle_enter_press(2)

                    elif self.current_page in 'account':
                        if home_btn and home_btn.is_over(mouse_pos):
                            self.current_page = 'home'
                        elif change_username_btn and change_username_btn.is_over(mouse_pos):
                            self.current_page = 'info_edit_username'
                        elif change_password_btn and change_password_btn.is_over(mouse_pos):
                            self.current_page = 'info_edit_password'
                        elif delete_account_btn and delete_account_btn.is_over(mouse_pos):
                            self.on_delete_account_click()
                    elif self.current_page in ['info_edit_username', 'info_edit_password']:
                        if submit_acc_btn and submit_acc_btn.is_over(mouse_pos):
                            if self.current_page == 'info_edit_username':
                              self.on_submit_username_click()
                            elif self.current_page == 'info_edit_password':
                             self.on_submit_password_click()
                        elif back_acc_btn and back_acc_btn.is_over(mouse_pos):
                            self.current_page = 'account'
                    elif self.current_page in 'matching_history':
                        if home_btn and home_btn.is_over(mouse_pos):
                            self.current_page = 'home'
                    elif self.current_page == 'new_game':
                        if enter_btn and enter_btn.is_over(mouse_pos):
                            self.move_player()
                        elif home_btn and home_btn.is_over(mouse_pos):
                            self.current_page = 'home'
                            self.timer_started = False
                            self.user_past_moves = []
                            self.engine_past_moves = []
                    elif self.current_page == 'registration':
                        if register_btn and register_btn.is_over(mouse_pos):
                            # perform signup operations
                            self.on_signup_click(self.username_input.text, self.email_input.text, self.password_input.password)
                            self.current_page = 'home'
                        elif back_log_btn and back_log_btn.is_over(mouse_pos):
                            self.current_page = 'login'
                            self.incorrect_password = False
                    elif self.current_page == 'registration':
                        if submit_acc_btn and submit_acc_btn.is_over(mouse_pos):
                            if self.current_page == 'info_edit_username':
                                self.on_submit_username_click()
                            elif self.current_page == 'info_edit_password':
                                self.on_submit_password_click()
                            elif back_acc_btn and back_acc_btn.is_over(mouse_pos):
                                self.current_page = 'account_page'
                    elif self.current_page == 'times_up':
                        if home_btn and home_btn.is_over(mouse_pos):
                            self.current_page = 'home'

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        if self.current_page == 'new_game':
                            self.move_player()
                        elif self.current_page == 'pvp':
                            self.handle_enter_press(self.current_player)


            # Update the display
            pygame.display.flip()
            clock.tick(60)

        pygame.quit()



# Main execution block
if __name__ == "__main__":
    app = CheckmateEngine()
    #app.start_new_game()
    app.run()
