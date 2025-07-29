import logging

def process_data(data):
    print(f"Starting process with {len(data)} items")

    for item in data:
        if item.get('debug'):
            print(f"Debug: {item}")

        # Process item
        result = transform(item)

        if result is None:
            print(f"Warning: Failed to process {item['id']}")

    print("Process completed")
