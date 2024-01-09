import tkinter as tk
from tkinter import messagebox
import engine

def on_button_click(option):
    print("on button click")
    if(option == 4):
        run_user_vs_engine()


def run_user_vs_engine():
    print("running user vs engine")
    engine.player_vs_engine()


def main():
    print("in main")
    root = tk.Tk()
    root.title("Options Menu")
    options = ["Login", "Make position", "Option 3", "User vs Engine"]
    # Create buttons for each option
    for i, option_text in enumerate(options, start=1):
        button = tk.Button(root, text=option_text, command=lambda i=i: on_button_click(i))
        button.pack(pady=10)

    root.mainloop()

if __name__ == "__main__":
    main()

