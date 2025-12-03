import csv
import random
from tkinter import Tk, simpledialog

def generate_random_fiscal_code():
    while True:
        code = str(random.randint(10000000000, 99999999999))
        if code.startswith("0"):
            code = code.replace("0", "1", 1)
        return code

def populate_files(input_file1, input_file2, n_rows, starting_order_code):
    # Read input files
    with open(input_file1, "r", newline="", encoding="utf-8") as file1, \
         open(input_file2, "r", newline="", encoding="utf-8") as file2:
        reader1 = list(csv.reader(file1, delimiter=";"))
        reader2 = list(csv.reader(file2, delimiter=";"))

    # Extract headers and template row (row 2)
    headers1, template_row1 = reader1[0], reader1[1]
    headers2, template_row2 = reader2[0], reader2[1]


    # Prepare new rows
    new_rows1 = []
    new_rows2 = []

    # Definizione dei dati fissi per tutti e 4 i prodotti
    product_data = {
        "Product1": {
            "ProductCode": "48-2MS10-25F0200",
            "ProductCodeEx": "3019",
            "PriceEx": "98.0000",
            "AvailabilityDate": "2025-10-01"
        },
        "Product2": {
            "ProductCode": "48-2MS10-25F0201",
            "ProductCodeEx": "3020",
            "PriceEx": "52.0000",
            "AvailabilityDate": "2025-10-01"
        },
        "Product3": {
            "ProductCode": "48-2MS10-25F0202",
            "ProductCodeEx": "3021",
            "PriceEx": "39.0000",
            "AvailabilityDate": "2025-10-01"
        },
        "Product4": {
            "ProductCode": "48-2MS10-25F0997",
            "ProductCodeEx": "3014",
            "PriceEx": "80.00",
            "AvailabilityDate": "2025-10-05"
        }
    }

    for i in range(n_rows):
        order_code = starting_order_code + i

        # Generate random FiscalCode and VATNumber
        fiscal_code = generate_random_fiscal_code()

        # Populate input_request2_easy.csv
        new_row2 = template_row2.copy()
        new_row2[headers2.index("FiscalCode")] = fiscal_code
        new_row2[headers2.index("VATNumber")] = fiscal_code
        new_row2[headers2.index("OrderCodeEx")] = str(order_code)
        new_row2[headers2.index("OrderCodeID")] = str(order_code)
        new_row2[headers2.index("InvoiceName1")] = f"SocietaTest{order_code}"
        new_row2[headers2.index("ShopID")] = f"PHEY-{order_code}"

        # Popola prodotti casualmente
        selected_products = random.sample(list(product_data.keys()), random.randint(1, len(product_data)))
        total_price = 0

        for j, product_key in enumerate(selected_products, start=1):
            item_code_col = f"Product{j}_ItemCode"
            product_code_col = f"Product{j}_ProductCode"
            product_code_ex_col = f"Product{j}_ProductCodeEx"
            price_col = f"Product{j}_PriceEx"
            availability_date_col = f"Product{j}_AvailabilityDate"

            # Popola i dati del prodotto
            new_row2[headers2.index(item_code_col)] = f"{j * 10}"
            new_row2[headers2.index(product_code_col)] = product_data[product_key]["ProductCode"]
            new_row2[headers2.index(product_code_ex_col)] = product_data[product_key]["ProductCodeEx"]
            
            # Mantieni il formato originale degli importi e calcola la somma correttamente
            # Formatta il prezzo con quattro decimali
            formatted_price = f"{float(product_data[product_key]['PriceEx']):.4f}"
            new_row2[headers2.index(price_col)] = formatted_price
            total_price += float(formatted_price)

            # Formatta la data nel formato 'aaaa-mm-gg'
            formatted_date = product_data[product_key]['AvailabilityDate']
            new_row2[headers2.index(availability_date_col)] = formatted_date

        new_row2[headers2.index("Total")] = f"{total_price:.2f}"
        new_rows2.append(new_row2)

        # Cancella i dati per i prodotti non selezionati
        for j in range(len(selected_products) + 1, 5):
            item_code_col = f"Product{j}_ItemCode"
            product_code_col = f"Product{j}_ProductCode"
            product_code_ex_col = f"Product{j}_ProductCodeEx"
            price_col = f"Product{j}_PriceEx"
            availability_date_col = f"Product{j}_AvailabilityDate"

            new_row2[headers2.index(item_code_col)] = ""
            new_row2[headers2.index(product_code_col)] = ""
            new_row2[headers2.index(product_code_ex_col)] = ""
            new_row2[headers2.index(price_col)] = ""
            new_row2[headers2.index(availability_date_col)] = ""

            # Cancella anche le colonne aggiuntive per i prodotti non selezionati
            quantity_col = f"Product{j}_Quantity"
            product_type_col = f"Product{j}_ProductType"
            discount_col = f"Product{j}_Discount"
            discount_percentage_col = f"Product{j}_DiscountPercentage"

            new_row2[headers2.index(quantity_col)] = ""
            new_row2[headers2.index(product_type_col)] = ""
            new_row2[headers2.index(discount_col)] = ""
            new_row2[headers2.index(discount_percentage_col)] = ""

        # Populate input_request1_easy.csv
        new_row1 = template_row1.copy()
        new_row1[headers1.index("FiscalCode")] = fiscal_code
        new_row1[headers1.index("VATNumber")] = fiscal_code

        # Popola input_request1_easy.csv con i dati del file 2
        for j in range(1, 5):
            product_code_col = f"ProductCode{j}"
            product_code_ex_col = f"ProductCodeEx{j}"
            price_col_input1 = f"PriceEx{j}"
            price_col_input2 = f"Product{j}_PriceEx"

            if new_row2[headers2.index(f"Product{j}_ItemCode")]:
                new_row1[headers1.index(product_code_col)] = new_row2[headers2.index(f"Product{j}_ProductCode")]
                new_row1[headers1.index(product_code_ex_col)] = new_row2[headers2.index(f"Product{j}_ProductCode")]
                new_row1[headers1.index(price_col_input1)] = new_row2[headers2.index(price_col_input2)]
            else:
                new_row1[headers1.index(product_code_col)] = ""
                new_row1[headers1.index(product_code_ex_col)] = ""
                new_row1[headers1.index(price_col_input1)] = ""

        # Cancella i dati per i prodotti non selezionati anche nel file 1
        for j in range(len(selected_products) + 1, 5):
            product_code_col = f"ProductCode{j}"
            price_col_input1 = f"PriceEx{j}"

            new_row1[headers1.index(product_code_col)] = ""
            new_row1[headers1.index(price_col_input1)] = ""

            # Cancella anche le colonne aggiuntive per i prodotti non selezionati nel file 1
            quantity_col = f"Quantity{j}"
            product_type_col = f"ProductType{j}"
            discount_col = f"Discount{j}"
            discount_percentage_col = f"DiscountPercentage{j}"
            shipping_fee_col = f"ShippingFees{j}"

            new_row1[headers1.index(quantity_col)] = ""
            new_row1[headers1.index(product_type_col)] = ""
            new_row1[headers1.index(discount_col)] = ""
            new_row1[headers1.index(discount_percentage_col)] = ""
            new_row1[headers1.index(shipping_fee_col)] = ""

        # Mantieni la popolazione della colonna Total solo nel file input_request2_easy.csv
        # new_row1[headers1.index("Total")] = new_row2[headers2.index("Total")]
        new_rows1.append(new_row1)

    # Write output files
    with open(input_file1, "w", newline="", encoding="utf-8") as file1, \
         open(input_file2, "w", newline="", encoding="utf-8") as file2:
        writer1 = csv.writer(file1)
        writer2 = csv.writer(file2)

        writer1.writerow(headers1)
        writer1.writerows(new_rows1)

        writer2.writerow(headers2)
        writer2.writerows(new_rows2)

if __name__ == "__main__":
    # Initialize Tkinter for pop-up dialogs
    root = Tk()
    root.withdraw()

    # Ask for user input
    n_rows = simpledialog.askinteger("Input", "Enter the number of rows to populate:")
    starting_order_code = simpledialog.askinteger("Input", "Enter the starting OrderCode:")

    # File paths
    input_file1 = "input_request1_easy_Copy.csv"
    input_file2 = "input_request2_easy.csv"

    # Populate files
    populate_files(input_file1, input_file2, n_rows, starting_order_code)

    print("Files populated successfully!")