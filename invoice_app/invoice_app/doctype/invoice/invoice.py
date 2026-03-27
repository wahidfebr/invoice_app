import frappe
from frappe.model.document import Document
from frappe.model.naming import getseries


class Invoice(Document):
    def autoname(self):
        customer_name = frappe.db.get_value("Customer", self.customer, "customer_name")
        initials = "".join([word[0].upper() for word in customer_name.split() if word])
        posting_date = self.tanggal_terbit or frappe.utils.today()
        yymm = frappe.utils.getdate(posting_date).strftime("%y%m")
        prefix = f"INV/{initials}/{yymm}/"
        self.name = prefix + getseries(prefix, 5)

    def validate(self):
        self.customer_name = frappe.db.get_value("Customer", self.customer, "customer_name")
        self.calculate_totals()

    def calculate_totals(self):
        self.total_harga_item = 0
        for item in self.items:
            item.harga = item.kuantitas * item.rate
            self.total_harga_item += item.harga

        tax_amount = self.total_harga_item * (self.persentase_pajak or 0) / 100
        self.grand_total = self.total_harga_item + tax_amount
        self.outstanding_amount = self.grand_total - (self.payment_amount or 0)

        if self.payment_amount and self.payment_amount >= self.grand_total:
            self.payment_status = "Paid"
        elif self.payment_amount and self.payment_amount > 0:
            self.payment_status = "Partially Paid"
        else:
            self.payment_status = "Unpaid"
