def complex_function(data, threshold=10, debug=False):
    """Complex function with nested structures"""
    result = []

    for item in data:
        if item > 0:
            try:
                value = item * 2
                if value > 10:
                    result.append(value)
                else:
                    result.append(item)
            except Exception as e:
                print(f"Error: {e}")
                continue
        else:
            result.append(0)

    return result

class DataProcessor:
    def process(self, input_data):
        try:
            if not input_data:
                return None

            for item in input_data:
                if isinstance(item, dict):
                    self.data.append(item['value'])
                elif isinstance(item, list):
                    self.data.extend(item)
                else:
                    self.data.append(item)

        except KeyError as e:
            print(f"Key error: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")
        finally:
            print("Processing complete")
