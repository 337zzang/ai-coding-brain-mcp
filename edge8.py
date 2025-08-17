class DataProcessor:
    def process_data(self, data, transform=True, validate=True, normalize=True, filter_empty=True, sort_keys=True, remove_duplicates=True):
        if validate and data is None:
            raise ValueError("Data cannot be None")
        if transform and isinstance(data, list):
            processed_data = [item for item in data if item is not None] if filter_empty else data
            return sorted(list(set(processed_data))) if remove_duplicates else processed_data
        return data