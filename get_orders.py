import requests
import csv
from datetime import datetime
import os

# API URL
url = "https://api.lofty.ai/prod/properties/v2/marketplace?page=1&pageSize=200"
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


def fetch_and_save_orderbook(propertyId, assetUnit):
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


def analyze_orderbooks(output_dir, lp_only=False):
    all_orders = []

    # Iterate through all files in the output directory
    for fn in os.listdir(output_dir):
        if lp_only:
            with open("lp_list.txt", mode='r', newline='') as lp:
                lp_list = [x.rstrip() for x in lp.readlines()]

            # Skip files w/o liquidity pool
            if fn.split('_')[0] not in lp_list:
                print(fn.split('_')[0] + " has no LP")
                continue

        if "open_orders" in fn and "combined" not in fn:
            # Construct the full path to the file
            file_path = os.path.join(output_dir, fn)

            # Open each relevant CSV file and read the data
            with open(file_path, mode='r', newline='') as file:
                reader = csv.reader(file)
                headers = next(reader)  # Get the header row

                print(f"Headers in {fn}: {headers}")  # Print the headers to debug

                # Determine index of each column
                order_type_index = headers.index("Order Type")
                quantity_index = headers.index("Quantity")
                price_index = headers.index("Price")
                property_id_index = headers.index("Property ID")
                order_id_index = headers.index("Order ID")
                expire_at_index = headers.index("Expire At")
                created_at_index = headers.index("Created At")

                # Read each order and append to the all_orders list, replacing property_id with a link
                for row in reader:
                    # Create the link for the property ID
                    link = f"https://lofty.ai/property_deal/{row[property_id_index]}"

                    # Append order with the link instead of property ID
                    all_orders.append((
                        row[order_type_index],
                        int(row[quantity_index]),
                        float(row[price_index]),
                        link,  # Use the link here
                        row[order_id_index],
                        row[expire_at_index],
                        row[created_at_index]
                    ))

    # Sort the orders: 'Buy' orders first by price ascending, then 'Sell' orders by price ascending
    all_orders.sort(key=lambda x: (x[0], x[2]), reverse=True)

    # Write the combined and sorted orders to a new CSV file
    order_books_fn = "combined_open_orders_lp_only.csv" if lp_only else "combined_open_orders.csv"
    with open(os.path.join(output_dir, order_books_fn), mode='w', newline='') as file:
        writer = csv.writer(file)

        # Write the header row with updated 'Property Link' label
        writer.writerow(['Order Type', 'Quantity', 'Price', 'Property Link', 'Order ID', 'Expire At', 'Created At'])

        # Write sorted orders
        for order in all_orders:
            writer.writerow(order)


analyze_orderbooks(output_dir, True)


if '__name__' == '__main__':
    # Make the GET request``
    response = requests.get(url)

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

#main()  # Analysis of existing data only, don't get new data by default