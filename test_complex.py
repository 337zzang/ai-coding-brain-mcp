class Logger:
    def info(self, msg):
        print(f"INFO: {msg}")

    def error(self, msg):
        print(f"ERROR: {msg}")

logger = Logger()
logger.info("Starting")
print("Direct print")  # This is a print
