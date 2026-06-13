import subprocess
import pickle

def run_command(user_input):
    # Intentional vulnerability: command injection
    subprocess.run(user_input, shell=True)

def load_data(data):
    # Intentional vulnerability: unsafe deserialization
    return pickle.loads(data)

def evaluate(user_expr):
    # Intentional vulnerability: code execution
    return eval(user_expr)