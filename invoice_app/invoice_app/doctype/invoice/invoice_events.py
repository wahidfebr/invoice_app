import frappe
from frappe.model.naming import getseries
from frappe.utils import flt


def invoice_autoname(doc, method=None):
    nama = frappe.db.get_value("Customer", doc.customer, "nama_customer")
    if not nama:
        frappe.throw(f"Customer '{doc.customer}' tidak ditemukan")
    initials = "".join([word[0].upper() for word in nama.split() if word])
    posting_date = doc.tanggal_terbit or frappe.utils.today()
    yymm = frappe.utils.getdate(posting_date).strftime("%y%m")
    prefix = f"INV/{initials}/{yymm}/"
    doc.name = prefix + getseries(prefix, 5)


def invoice_validate(doc, method=None):
    doc.customer_name = frappe.db.get_value("Customer", doc.customer, "nama_customer")
    if not doc.items:
        frappe.throw("Invoice harus memiliki minimal 1 item")
    if flt(doc.persentase_pajak) < 0:
        frappe.throw("Persentase pajak tidak boleh kurang dari 0")
    validate_items(doc)
    calculate_totals(doc)


def validate_items(doc):
    for item in doc.items:
        if flt(item.rate) < 0:
            frappe.throw(f"Rate untuk item '{item.nama_item}' tidak boleh kurang dari 0")
        if flt(item.kuantitas) <= 0:
            frappe.throw(f"Kuantitas untuk item '{item.nama_item}' tidak boleh kurang dari sama dengan 0")


def calculate_totals(doc):
    doc.total_harga_item = 0
    for item in doc.items:
        item.harga = flt(item.kuantitas) * flt(item.rate)
        doc.total_harga_item += item.harga

    tax_amount = flt(doc.total_harga_item) * flt(doc.persentase_pajak) / 100
    doc.grand_total = flt(doc.total_harga_item) + tax_amount
    doc.outstanding_amount = flt(doc.grand_total) - flt(doc.payment_amount)

    if flt(doc.grand_total) == 0:
        doc.payment_status = "Paid"
    elif flt(doc.payment_amount) and flt(doc.payment_amount) >= flt(doc.grand_total):
        doc.payment_status = "Paid"
    elif flt(doc.payment_amount) and flt(doc.payment_amount) > 0:
        doc.payment_status = "Partially Paid"
    else:
        doc.payment_status = "Unpaid"
