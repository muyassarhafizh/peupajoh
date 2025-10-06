def log_to_file(message: str, log_file: str):
    with open(log_file, "a") as f:
        f.write(f"{message}\n")
