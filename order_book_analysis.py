import requests
import csv
from datetime import datetime

# API URL
url = "https://api.lofty.ai/prod/properties/v2/marketplace?page=1&pageSize=200"

# Make the GET request
response = requests.get(url)

output_dir = "outputs"

def save_transaction_history_to_csv(property_id, assetUnit):
    # Construct the API URL for the transaction history endpoint
    url = f"https://api.lofty.ai/prod/exchange/v2/getpropertyinfo?propertyId={property_id}"

    # Make the API call
    response = requests.get(url)

    if response.status_code == 200:
        transactions = response.json()['data']['transactions']

        # Use a timestamp in the filename to make it unique
        timestamp = datetime.now().strftime("%Y%m%d-%H-%M-%S")
        filename = f"{output_dir}/{assetUnit}_history_{timestamp}.csv"

        # Open a CSV file to write the data
        with open(filename, mode='w', newline='') as file:
            writer = csv.writer(file)

            # Write the header row
            writer.writerow(
                ['ID', 'Type', 'Quantity', 'Price', 'Amount Crypto', 'Payment Currency', 'Created At', 'Updated At'])

            # Write transaction data
            for txn in transactions:
                writer.writerow(
                    [txn['id'], txn.get('type', ''), txn['quantity'], txn['price'], txn.get('amountCrypto', ''),
                     txn.get('paymentCurrency', ''), txn['createdAt'], txn.get('updatedAt', '')])

        print(f"Transaction history saved to {filename}")
    else:
        print("Failed to fetch data from API. Status code:", response.status_code)


def analyze_orderbooks(propertyId, assetUnit):
    # API endpoint with the propertyId parameter
    url = f"https://api.lofty.ai/prod/exchange/v2/getpropertyorderbook?propertyId={propertyId}"

    # Make the GET request
    response = requests.get(url)

    # Check if the request was successful
    if response.status_code == 200:
        # Parse the JSON response
        data = response.json()

        # Ensure the response indicates success
        if data.get('success') and data.get('data'):
            orderBook = data['data'].get('orderBook', {})
            buyOrders = orderBook.get('buyOrders', [])
            sellOrders = orderBook.get('sellOrders', [])

            # Open or create a CSV file to write the data
            with open(f'{output_dir}/{assetUnit}_open_orders.csv', mode='w', newline='') as file:
                writer = csv.writer(file)

                # Write the header row
                writer.writerow(
                    ['Order Type', 'Quantity', 'Price', 'Property ID', 'Order ID', 'Expire At', 'Created At'])

                # Write data for each buy order
                for order in buyOrders:
                    writer.writerow(
                        ['Buy', order.get('quantity'), order.get('price'), order.get('propertyId'), order.get('id'),
                         order.get('expireAt'), order.get('createdAt')])

                # Write data for each sell order
                for order in sellOrders:
                    writer.writerow(
                        ['Sell', order.get('quantity'), order.get('price'), order.get('propertyId'), order.get('id'),
                         order.get('expireAt'), order.get('createdAt')])
        else:
            print("Failed to parse order book data from the response.")
    else:
        print("Failed to fetch data from API. Status code:", response.status_code)


# Proceed if the request was successful
if response.status_code == 200:
    # Parse the JSON response
    data = response.json()

    # Open a CSV file to write the data
    with open(f"{output_dir}/properties.csv", mode='w', newline='') as file:
        # Create a CSV writer
        writer = csv.writer(file)

        # Write the header row
        writer.writerow(['ID', 'Asset Unit', 'Address'])

        # Extract and write data for each property
        for property in data.get('data', {}).get('properties', []):
            # Extract needed values, handling missing data gracefully
            id = property.get('id', '')
            asset_unit = property.get('assetUnit', '')
            address = property.get('address', '')  # Directly use the address string

            # Write the property data to the CSV
            writer.writerow([id, asset_unit, address])

            fetch_and_save_orderbook(id, asset_unit)
            save_transaction_history_to_csv(id, asset_unit)
else:
    print("Failed to fetch data from API. Status code:", response.status_code)