class FileHandler:
    def read_file(self, filename):
        try:
            with open(filename, 'r') as f:
                return f.read()
        except FileNotFoundError:
            return None