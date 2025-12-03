import pandas as pd
from locust import HttpUser, task, between
import csv
from datetime import datetime, timedelta
import time
import threading

# Funzione aggiornata per mostrare il popup senza immagine

def show_popup_with_metrics(title: str, num_inputs: int, avg_time: float, total_time: float, auto_close_ms: int = 4000):
    try:
        import tkinter as tk
        from tkinter import ttk

        def _run():
            root = tk.Tk()
            root.title(title)
            root.attributes('-topmost', True)
            root.geometry('420x220+50+50')

            frm = ttk.Frame(root, padding=12)
            frm.pack(fill='both', expand=True)

            metrics_message = (
                f"Numero di input lavorati: {num_inputs}\n"
                f"Tempo medio per ognuno: {avg_time:.2f} ms\n"
                f"Tempo totale impiegato: {total_time:.2f} ms\n"
            )

            lbl = ttk.Label(frm, text=metrics_message, justify='left')
            lbl.pack(anchor='w')

            btn = ttk.Button(frm, text='Chiudi', command=root.destroy)
            btn.pack(anchor='e', pady=(10, 0))

            root.after(auto_close_ms, root.destroy)
            root.mainloop()

        threading.Thread(target=_run, daemon=True).start()
    except Exception:
        pass

# --- Helpers per output leggibile a schermo ---
def pretty_time(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

def print_banner(title: str):
    line = "=" * 60
    print(f"\n{line}\n{title}\n{line}")

def print_timing(name: str, start: datetime, end: datetime):
    duration_ms = (end - start).total_seconds() * 1000
    print_banner(f"{name}")
    print(f"Start:   {pretty_time(start)}")
    print(f"End:     {pretty_time(end)}")
    print(f"Duration: {duration_ms:.1f} ms")

# Funzione per salvare i dati della risposta in un file Excel

def save_response_to_excel(response_data, file_path):
    try:
        df = pd.DataFrame(response_data)
        df.to_excel(file_path, index=False)
        print(f"Dati salvati in {file_path}")
    except Exception as e:
        print(f"Errore durante il salvataggio in Excel: {e}")

# --- Funzioni di utilità comuni ---
def safe_value(val):
    if pd.isna(val) or val is None or str(val).strip().lower() in ["nan", "none", ""]:
        return None
    return val

def xml_tag(tag, value):
    if value is None or str(value).strip() == "":
        return f"<{tag}/>"
    return f"<{tag}>{value}</{tag}"

# Carica i dati dai due file CSV
input1 = pd.read_csv("input_request1_easy.csv", dtype={"VATNumber": str, "FiscalCode": str})
rows1 = input1.to_dict(orient="records")
input2 = pd.read_csv("input_request2_easy.csv", dtype=str)
rows2 = input2.to_dict(orient="records")

# --- Sincronizzazione di avvio simultaneo ---
# Imposta l'orario di start al prossimo secondo pieno
_now = datetime.now()
# Usa timedelta della libreria standard invece di pd.Timedelta e evita to_pydatetime()
START_AT = _now.replace(microsecond=0) + timedelta(seconds=1)

def wait_until_start():
    while datetime.now() < START_AT:
        # sleep in piccoli intervalli per precisione
        time.sleep(0.005)

PRODUCT_TEMPLATE = '''    <ns1:Product>\n        <ns1:ItemCode>{ItemCode}</ns1:ItemCode>\n        <ns1:ProductCode>{ProductCode}</ns1:ProductCode>\n        <ns1:ProductCodeEx>{ProductCodeEx}</ns1:ProductCodeEx>\n        <ns1:Quantity>{Quantity}</ns1:Quantity>\n        <ns1:ProductType>{ProductType}</ns1:ProductType>\n        <ns1:Discount>{Discount}</ns1:Discount>\n        <ns1:DiscountPercentage>{DiscountPercentage}</ns1:DiscountPercentage>\n        <ns1:ShippingFees>{ShippingFees}</ns1:ShippingFees>\n        <ns1:PriceEx>{PriceEx}</ns1:PriceEx>\n        <ns1:Customizations>{Customizations}</ns1:Customizations>\n    </ns1:Product>'''

SOAP1_TEMPLATE = '''<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" xmlns:ns1="http://www.ipzs.it/ecommerce/b2b/types/1.0">\n    <SOAP-ENV:Body>\n        <ns1:OrderSimulationRequest>\n            <ns1:Application>{Application}</ns1:Application>\n            <ns1:CustomerType>{CustomerType}</ns1:CustomerType>\n            <ns1:CustomerCode>{CustomerCode}</ns1:CustomerCode>\n            <ns1:CustomerCodeEx>{CustomerCodeEx}</ns1:CustomerCodeEx>\n            <ns1:FiscalCode>{FiscalCode}</ns1:FiscalCode>\n            <ns1:VATNumber>{VATNumber}</ns1:VATNumber>\n            <ns1:CountryISO>{CountryISO}</ns1:CountryISO>\n            <ns1:Region>{Region}</ns1:Region>\n            <ns1:City>{City}</ns1:City>\n            <ns1:InvoiceCountryISO>{InvoiceCountryISO}</ns1:InvoiceCountryISO>\n            <ns1:IPACode>{IPACode}</ns1:IPACode>\n            <ns1:OrderCode>{OrderCode}</ns1:OrderCode>\n            <ns1:ProductList>\n{product_xml}\n            </ns1:ProductList>\n        </ns1:OrderSimulationRequest>\n    </SOAP-ENV:Body>\n</SOAP-ENV:Envelope>'''

# --- Request 1: costruzione dinamica lista prodotti ---
class Request1User(HttpUser):
    wait_time = between(1, 2)
    host = "https://pzs.sap.ipzs.it"
    data_index = 0
    total_requests = 0
    total_time_ms = 0

    @task
    def send_request1(self):
        # Attende la barriera di start per sincronizzarsi con Request2
        wait_until_start()
        start_ts = datetime.now()
        if not rows1:
            return
        row = rows1[self.data_index % len(rows1)]
        self.data_index += 1

        products = []
        for i in range(1, 6):
            if safe_value(row.get(f"ItemCode{i}")):
                products.append({
                    "ItemCode": safe_value(row.get(f"ItemCode{i}", "")),
                    "ProductCode": safe_value(row.get(f"ProductCode{i}", "")),
                    "ProductCodeEx": safe_value(row.get(f"ProductCodeEx{i}", "")),
                    "Quantity": safe_value(row.get(f"Quantity{i}", "")),
                    "ProductType": safe_value(row.get(f"ProductType{i}", "")),
                    "Discount": safe_value(row.get(f"Discount{i}", "")),
                    "DiscountPercentage": safe_value(row.get(f"DiscountPercentage{i}", "")),
                    "ShippingFees": safe_value(row.get(f"ShippingFees{i}", "")),
                    "PriceEx": safe_value(row.get(f"PriceEx{i}", "")),
                    "Customizations": safe_value(row.get(f"Customizations{i}", ""))
                })

        product_xml = "\n".join([
            "    <ns1:Product>" +
            "".join([
                "\n        " + xml_tag(f"ns1:{k}", v) for k, v in prod.items()
            ]) +
            "\n    </ns1:Product>"
            for prod in products
        ])

        row_fmt = {k: safe_value(v) for k, v in row.items()}
        soap_body = SOAP1_TEMPLATE
        for k, v in row_fmt.items():
            soap_body = soap_body.replace(f"{{{k}}}", str(v) if v is not None else "")
        soap_body = soap_body.replace("{product_xml}", product_xml)
        headers = {"Content-Type": "text/xml; charset=utf-8", "SOAPAction": ""}

        response = self.client.post(
            "/sap/bc/srt/xip/sap/zecommerce/400/ecommerce/ecommerce",
            data=soap_body,
            headers=headers,
            name="OrderSimulationRequest"
        )

        end_ts = datetime.now()
        duration_ms = (end_ts - start_ts).total_seconds() * 1000
        self.total_requests += 1
        self.total_time_ms += duration_ms

        avg_time_ms = self.total_time_ms / self.total_requests

        # Mostra il popup con le metriche
        show_popup_with_metrics(
            "OrderSimulationRequest Metrics",
            self.total_requests,
            avg_time_ms,
            self.total_time_ms
        )

        # Salva la risposta in un file Excel
        response_data = [{"status_code": response.status_code, "content": response.text}]
        save_response_to_excel(response_data, "response_data.xlsx")

# --- Request 2: costruzione dinamica ProductList e Order ---
def build_address_xml(prefix, row):
    tel = row.get(f'{prefix}Telephone')
    fax = row.get(f'{prefix}FAX')
    email = row.get(f'{prefix}Email')
    return (f"<ns1:Address>\n"
        f"  {xml_tag('ns1:Name1', row.get(f'{prefix}Name1'))}\n"
        f"  {xml_tag('ns1:Name2', row.get(f'{prefix}Name2'))}\n"
        f"  {xml_tag('ns1:City', row.get(f'{prefix}City'))}\n"
        f"  {xml_tag('ns1:PostalCode', row.get(f'{prefix}PostalCode'))}\n"
        f"  {xml_tag('ns1:Street', row.get(f'{prefix}Street'))}\n"
        f"  {xml_tag('ns1:HouseNumber', row.get(f'{prefix}HouseNumber'))}\n"
        f"  {xml_tag('ns1:Region', row.get(f'{prefix}Region'))}\n"
        f"  {xml_tag('ns1:CountryISO', row.get(f'{prefix}CountryISO'))}\n"
        f"  {xml_tag('ns1:LanguageISO', row.get(f'{prefix}LanguageISO'))}\n"
        f"  <ns1:TelephoneList>\n"
        f"    <ns1:Telephone>\n"
        f"      <ns1:NumTelephone>{tel if tel else ''}</ns1:NumTelephone>\n"
        f"    </ns1:Telephone>\n"
        f"  </ns1:TelephoneList>\n"
        f"  <ns1:FAXList>\n"
        f"    <ns1:FAX>\n"
        f"      <ns1:NumFAX>{fax if fax else ''}</ns1:NumFAX>\n"
        f"    </ns1:FAX>\n"
        f"  </ns1:FAXList>\n"
        f"  <ns1:EmailList>\n"
        f"    <ns1:Email>\n"
        f"      <ns1:AddresseMail>{email if email else ''}</ns1:AddresseMail>\n"
        f"    </ns1:Email>\n"
        f"  </ns1:EmailList>\n"
        f"</ns1:Address>")

def build_product_xml(row):
    products = []
    for i in range(1, 6):
        prefix = f'Product{i}_'
        if safe_value(row.get(f'{prefix}ItemCode')):
            products.append(
                f"<ns1:Product>\n"
                f"  {xml_tag('ns1:ItemCode', row.get(f'{prefix}ItemCode'))}\n"
                f"  {xml_tag('ns1:ProductCode', row.get(f'{prefix}ProductCode'))}\n"
                f"  {xml_tag('ns1:ProductCodeEx', row.get(f'{prefix}ProductCodeEx'))}\n"
                f"  {xml_tag('ns1:Quantity', row.get(f'{prefix}Quantity'))}\n"
                f"  {xml_tag('ns1:ProductType', row.get(f'{prefix}ProductType'))}\n"
                f"  {xml_tag('ns1:Discount', row.get(f'{prefix}Discount'))}\n"
                f"  {xml_tag('ns1:DiscountPercentage', row.get(f'{prefix}DiscountPercentage'))}\n"
                f"  {xml_tag('ns1:PriceEx', row.get(f'{prefix}PriceEx'))}\n"
                f"  {xml_tag('ns1:AvailabilityDate', row.get(f'{prefix}AvailabilityDate'))}\n"
                f"</ns1:Product>"
            )
    return "\n".join(products)

def build_order_xml(row):
    return (f"<ns1:Order>\n"
            f"  {xml_tag('ns1:OrderCodeEx', row.get('OrderCodeEx'))}\n"
            f"  {xml_tag('ns1:OrderCodeID', row.get('OrderCodeID'))}\n"
            f"  {xml_tag('ns1:OperationType', row.get('OperationType'))}\n"
            f"  {xml_tag('ns1:Total', row.get('Total'))}\n"
            f"  {xml_tag('ns1:ShippingFees', row.get('OrderShippingFees'))}\n"
            f"  <ns1:InvoiceAddress>\n"
            f"{build_address_xml('Invoice', row)}\n"
            f"  </ns1:InvoiceAddress>\n"
            f"  <ns1:ShippingAddress>\n"
            f"{build_address_xml('Shipping', row)}\n"
            f"  </ns1:ShippingAddress>\n"
            f"  {xml_tag('ns1:Retreat', row.get('Retreat'))}\n"
            f"  {xml_tag('ns1:PaymentType', row.get('PaymentType'))}\n"
            f"  {xml_tag('ns1:PaymentDate', row.get('PaymentDate'))}\n"
            f"  {xml_tag('ns1:Ksig', row.get('Ksig'))}\n"
            f"  {xml_tag('ns1:TerminalID', row.get('TerminalID'))}\n"
            f"  {xml_tag('ns1:ShopID', row.get('ShopID'))}\n"
            f"  {xml_tag('ns1:RefTranID', row.get('RefTranID'))}\n"
            f"  {xml_tag('ns1:PaymentID', row.get('PaymentID'))}\n"
            f"  <ns1:ProductList>\n"
            f"{build_product_xml(row)}\n"
            f"  </ns1:ProductList>\n"
            f"</ns1:Order>")

SOAP2_TEMPLATE = '''<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" xmlns:ns1="http://www.ipzs.it/ecommerce/b2b/types/1.0">\n    <SOAP-ENV:Body>\n        <ns1:OrderRequest>\n            {main_tags}\n            {order_xml}\n        </ns1:OrderRequest>\n    </SOAP-ENV:Body>\n</SOAP-ENV:Envelope>'''

class Request2User(HttpUser):
    wait_time = between(1, 2)
    host = "https://pzs.sap.ipzs.it"
    data_index = 0

    @task
    def send_request2(self):
        # Attende la barriera di start per sincronizzarsi con Request1
        wait_until_start()
        start_ts = datetime.now()
        if not rows2:
            return
        row = rows2[self.data_index % len(rows2)]
        self.data_index += 1
        main_tags = "\n".join([
            xml_tag('ns1:Application', row.get('Application')),
            xml_tag('ns1:CustomerType', row.get('CustomerType')),
            xml_tag('ns1:CustomerCode', row.get('CustomerCode')),
            xml_tag('ns1:CustomerCodeEx', row.get('CustomerCodeEx')),
            xml_tag('ns1:FiscalCode', row.get('FiscalCode')),
            xml_tag('ns1:VATNumber', row.get('VATNumber')),
            xml_tag('ns1:PEC', row.get('PEC')),
            xml_tag('ns1:SDICode', row.get('SDICode'))
        ])
        order_xml = build_order_xml(row)
        soap_body = SOAP2_TEMPLATE.format(main_tags=main_tags, order_xml=order_xml)
        headers = {"Content-Type": "text/xml; charset=utf-8", "SOAPAction": ""}
        response = self.client.post(
            "/sap/bc/srt/xip/sap/zecommerce/400/ecommerce/ecommerce",
            data=soap_body,
            headers=headers,
            name="OrderRequest"
        )
        end_ts = datetime.now()
        print_timing("OrderRequest", start_ts, end_ts)

        # Mostra il popup con le metriche per Request2
        show_popup_with_metrics(
            "OrderRequest Metrics",  # Titolo aggiornato per Request2
            self.data_index,  # Numero di richieste inviate
            (end_ts - start_ts).total_seconds() * 1000,  # Tempo medio per richiesta
            (end_ts - START_AT).total_seconds() * 1000  # Tempo totale dall'inizio
        )
