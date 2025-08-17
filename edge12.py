class FunctionalProcessor:
    def process_list(self, items, multiplier=2, filter_func=None):
        # Advanced functional processing
        filter_func = filter_func or (lambda x: x > 0)
        filtered = [x for x in items if filter_func(x)]
        mapped = [x * multiplier for x in filtered]  # List comprehension instead of map
        sorted_result = sorted(mapped, reverse=True)
        return sorted_result