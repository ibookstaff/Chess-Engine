import chess, random, sys, uci, time, pg, math
import chess.polyglot
import chess.engine
from boardevaluator import evaluate

board = chess.Board()
printedBoard = []
legalMoves = []
firstGo = True
valid_move = False
message = ""
player_move = None
enemy_move = None
count = 0
DEPTH = 3
OPENING_BOOK = "data/komodo.bin"


def check_game_over():
    global board
    result = {
        'message': '',
        'is_game_over': False,
        'winner': None,  # 'white', 'black', or 'draw'
    }

    if board.is_checkmate():
        result['message'] = "checkmate, Game over"
        result['is_game_over'] = True
        result['winner'] = 'white' if board.turn == chess.BLACK else 'black'
        return result

    if board.is_stalemate() or board.is_insufficient_material() or board.can_claim_draw():
        result['message'] = "draw, Game over"
        result['is_game_over'] = True
        result['winner'] = 'draw'
        return result

    # You can add more conditions for draw or victory if necessary

    return result



def check_opening_book():
    global board, OPENING_BOOK
    # using the chess.polygot feature, open the book to search
    best_move = None
    best_move_weight = -9999
    # can switch the path with the other books to test which book works the best
    with chess.polyglot.open_reader(OPENING_BOOK) as reader:
        # iterate over the moves in the book
        for entry in reader.find_all(board):
            # try to read the entry
            try:
                # check if its a better move
                if entry.weight > best_move_weight:
                    best_move = entry.move
                    best_move_weight = entry.weight
                    
            # some error occurred and the move was not found
            except Exception as e:
                print("Key was not found in the opening book: ", e)
                return None
    # returns the best move or None otherwise if not found
    return best_move

def checkmate_path(board):
    # assume there is a checkmate and try to prove false
    moves = board.legal_moves
    if moves is None:
        return True
    playerMoveCount = len(list(moves))
    checkmateCount = 0

    # this is iterating through the players possible moves
    for move in moves:
        board.push(move)

        engine_moves = board.legal_moves

        # iterate through the engine moves to see if there is a checkmate available
        hasCheckmate = False
        for eMove in engine_moves:
            # want to check if there still exists and engine move that will still result in checkmate
            hasCheckmate = False
            board.push(eMove)
            # check if it allows for checkmate
            if check_game_over() == "checkmate, Game over":
                hasCheckmate = True
                board.pop()
                break
            board.pop()
        if hasCheckmate:
            checkmateCount += 1
        
        #undo the current player move
        board.pop()
    # if the count of checkmates is equal to the or greater than the number of players move, we
    # have a checkmate option for whatever the player does
    if checkmateCount >= playerMoveCount:
        return True
    else:
        return False




# method to get the best move starting from the root (current board)
def minimaxRoot(board, depth, is_white):
    # if game is still in opening, use opening book moves
    move = check_opening_book()
    if move is not None:
        return move
    # have curr best moves for color set as max negatives
    best_move = -100000 if is_white else 100000
    best_final = None
    # iterate through all possible moves from the list
    for move in board.legal_moves:
        # push the move in the list
        board.push(move)
        # get the value of the board after this move
        value = minimax(depth - 1, board, -10000, 10000, not is_white)
        
        if check_game_over() == "checkmate, Game over":
            board.pop()
            return move
        if checkmate_path(board):
            board.pop()
            return move
        # undo the move from the board and reset board to before the move was made
        board.pop()
        # check if a new best move / end scenario was found
        if (is_white and value > best_move) or (not is_white and value < best_move):
            best_move = value
            best_final = move
    # return the best move found
    return best_final


# alpha beta pruning recursive minimax algorithm, finds best move based on goal / color (maximize own score if white / minimze opponent score if black)
def minimax(depth, board, alpha, beta, is_white):
    # base case of recursive search
    if depth <= 0 or board.is_game_over():
        return evaluate(board)

    # if we are white / trying to maximize our score
    if is_white:
        # assume a worst move that should be immediately replaced then iterate through the moves
        best_move = -100000
        for move in board.legal_moves:
            board.push(move)
            # recursively call minimax to coninue searching down the tree for best value
            value = minimax(depth - 1, board, alpha, beta, False)
            # undo the move
            board.pop()
            # return best available move
            best_move = max(best_move, value)
            # see if this is best move in subtree to speed up process
            alpha = max(alpha, best_move)
            if beta <= alpha:
                break
        return best_move
    else: # else we are black and trying to minimize the opponent
        best_move = 100000
        for move in board.legal_moves:
            # recursively call minimax to coninue searching down the tree for best value
            board.push(move)
            value = minimax(depth - 1, board, alpha, beta, True)
            board.pop()
            best_move = min(best_move, value)
            # see if this is best move in subtree to speed up process
            beta = min(beta, best_move)
            if beta <= alpha:
                break
        return best_move


def player_turn(p_move):
    global message, board, player_move, valid_move
    print(check_game_over())
    valid_move = False
    # check if the move made was valid
    for move in list(board.legal_moves):
        if str(move) == p_move:
            board.push(chess.Move.from_uci(p_move))
            player_move = convert_move(p_move, "white")
            valid_move = True
            break
    # if the move was invalid then return and have this tried again
    if not valid_move:
        message = "Invalid move. Please try again."
        return
    # check if the board is in checkmate
    print(check_game_over())

    print_unicode_board(chess.WHITE)


def enemy_turn():
    global enemy_move, board, message, DEPTH
    # call the minimax to find the engines move... alter 4 to reduce runtime but also will decrease move accuracy
    if check_game_over() == "checkmate, Game over":
        print("Game over, you beat the computer")
    if check_game_over() == "stalemate, Game over":
        print("Game over, you beat the computer")
    
    move = minimaxRoot(board, DEPTH, False)
    enemy_move = convert_move(str(move), "white")
    board.push(chess.Move.from_uci(str(move)))
    print_unicode_board(chess.WHITE)
    set_legal_moves()
    print(check_game_over())
    # Return the move made by the engine
    return str(move)


def convert_move(move, color):
    if color == "white":
        letters = ["", "a", "b", "c", "d", "e", "f", "g", "h"]
    else:
        letters = ["", "h", "g", "f", "e", "d", "c", "b", "a"]
    for index in range(4):
        if index % 2 == 0:
            move = move[:index] + str(letters.index(move[index])) + move[index + 1:]
        else:
            move = move[:index] + str((int(move[index]) - 8) * -1) + move[index + 1:]
    return move


# def get_user_color():
#     color = ""
#     while color not in ("white", "black"):
#         color = input("Do you want to be white or black? ")
#     return chess.WHITE if color == "white" else chess.BLACK

# This method prints out the board using piece types stored in the chess library
# and creates a board based off of chosen colors that has indexes for rows and columns
def print_unicode_board(perspective=chess.WHITE):
    """Prints the position from a given perspective."""
    space = u"\u2002"
    global printedBoard, board
    printedBoard = []
    for r in range(8) if perspective == chess.BLACK else range(7, -1, -1):
        # run through rows in chess board else range is  so that it flips board around
        line = [str(r + 1) + " "]
        # line for row of chess board setting format, +1 is for printing the labels for rows and columns
        for c in range(8) if perspective == chess.WHITE else range(7, -1, -1):
            piece = board.piece_at(8 * r + c)  # get piece from board
            line.append(
                # add piece to the line of pieces if it is a piece so we can print it later else just leave square blank
                (chess.UNICODE_PIECE_SYMBOLS[piece.symbol()] if piece else space + space)
            )
        chess_pieces = ""
        for piece in line:
            chess_pieces = chess_pieces + piece
        printedBoard.append(chess_pieces)
    letters = ["a", "b", "c", "d", "e", "f", "g", "h"]
    index_line = space
    if perspective == chess.WHITE:
        for letter in letters:
            index_line = index_line + space + letter
        printedBoard.append(index_line)
    else:
        for letter in letters.reverse():
            index_line = index_line + space + letter
        printedBoard.append(index_line)


def set_legal_moves():
    global legalMoves, board
    legalMoves = []
    i = 0
    for move in list(board.legal_moves):
        i = i + 1
        move_str = str(move)
        if i < len(list(board.legal_moves)):
            move_str = move_str + ", "
        legalMoves.append(move_str)


def first_load():
    set_legal_moves()
    print_unicode_board(chess.WHITE)


def reset():
    global board, printedBoard, legalMoves, firstGo, message, player_move, enemy_move, valid_move
    board = chess.Board()
    printedBoard = []
    legalMoves = []
    firstGo = True
    message = ""
    player_move = None
    enemy_move = None
    first_load()
