import frappe
from frappe.model.naming import getseries


def invoice_autoname(doc, method=None):
    nama = frappe.db.get_value("Customer", doc.customer, "nama_customer")
    initials = "".join([word[0].upper() for word in nama.split() if word])
    posting_date = doc.tanggal_terbit or frappe.utils.today()
    yymm = frappe.utils.getdate(posting_date).strftime("%y%m")
    prefix = f"INV/{initials}/{yymm}/"
    doc.name = prefix + getseries(prefix, 5)


def invoice_validate(doc, method=None):
    doc.customer_name = frappe.db.get_value("Customer", doc.customer, "nama_customer")
    calculate_totals(doc)


def calculate_totals(doc):
    doc.total_harga_item = 0
    for item in doc.items:
        item.harga = item.kuantitas * item.rate
        doc.total_harga_item += item.harga

    tax_amount = doc.total_harga_item * (doc.persentase_pajak or 0) / 100
    doc.grand_total = doc.total_harga_item + tax_amount
    doc.outstanding_amount = doc.grand_total - (doc.payment_amount or 0)

    if doc.payment_amount and doc.payment_amount >= doc.grand_total:
        doc.payment_status = "Paid"
    elif doc.payment_amount and doc.payment_amount > 0:
        doc.payment_status = "Partially Paid"
    else:
        doc.payment_status = "Unpaid"
