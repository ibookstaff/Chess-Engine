import engine, logger
import chess, random, sys, uci, time, pg, math


print("How many games do we want to run?")
iterations = input()

# generates a random move to test against
def generateRandomMove(board):
    print("random")
    moves = list(board.legal_moves)
    if moves:
        return random.choice(moves)
    else: 
        return None

# generates a move from our engine
def generateEngineMove(board):
    move = engine.minimaxRoot(board, 3, True)
    return move


# list for the moves over iterations
moveCounts = []

# overall game we are running
for i in range(0,int(iterations)):
    print(i)
    # white
    player1 = None
    #black
    player2 = None
    engine.reset()
    move_count = 0
    # while the game isn't over, keep making moves
    while(True):
        try:
            # generate a random move for WHITE
            move = generateRandomMove(engine.board)
            print(move)
            engine.board.push(chess.Move.from_uci(str(move)))
            
            # check if the game has concluded and break if needed
            if engine.check_game_over() == "checkmate, Game over":
                print("White wins with checkmate")
                logger.write_for_successful_run("Game ended in ccheckmate, White wins after move: " + str(move_count))
                moveCounts.append(move_count)
                break
            if engine.check_game_over() == "stalemate, Game over":
                logger.write_for_successful_run("Draw after move: " + str(move_count))
                print("Draw")
                moveCounts.append(move_count)
                break

            print(engine.board)
            print("////////////////////////////////////////")
            # generate an engine move for BLACK
            move = generateEngineMove(engine.board)
            engine.board.push(chess.Move.from_uci(str(move)))

            # check if the game has concluded and break if needed
            if engine.check_game_over() == "checkmate, Game over":
                print("Game ended in ccheckmate, Black wins")
                logger.write_for_successful_run("Game ended in ccheckmate, Black wins after move: " + str(move_count))
                moveCounts.append(move_count)          
                break

            if engine.check_game_over() == "stalemate, Game over":
                logger.write_for_successful_run("Draw after move: " + str(move_count))
                print("Draw")
                moveCounts.append(move_count)
                break


            print(engine.board)
            move_count += 1

            print("////////////////////////////////////////")
        except Exception as e:
            logger.write_for_error(str(e)+": after move: " + str(move_count))
            break

logger.write_average_move_sim("The average moves needed are: " + str(sum(moveCounts) / len(moveCounts)))



