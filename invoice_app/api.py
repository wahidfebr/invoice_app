import frappe
from frappe import _


@frappe.whitelist()
def get_invoice(invoice_number):
    """
    GET /api/method/invoice_app.api.get_invoice?invoice_number=INV/W/2603/00001
    """
    if not invoice_number:
        frappe.throw(_("Invoice number is required"), frappe.MandatoryError)

    if not frappe.db.exists("Invoice", invoice_number):
        frappe.throw(
            _("Invoice {0} not found").format(invoice_number),
            frappe.DoesNotExistError
        )

    invoice = frappe.get_doc("Invoice", invoice_number)
    return invoice.as_dict()


@frappe.whitelist()
def mark_as_paid(invoice_number, payment_amount):
    """
    POST /api/method/invoice_app.api.mark_as_paid
    Body: { "invoice_number": "INV/W/2603/00001", "payment_amount": 10000 }
    """
    if not invoice_number:
        frappe.throw(_("Invoice number is required"), frappe.MandatoryError)

    if not payment_amount:
        frappe.throw(_("Payment amount is required"), frappe.MandatoryError)

    payment_amount = float(payment_amount)

    if payment_amount <= 0:
        frappe.throw(_("Payment amount must be greater than 0"))

    if not frappe.db.exists("Invoice", invoice_number):
        frappe.throw(
            _("Invoice {0} not found").format(invoice_number),
            frappe.DoesNotExistError
        )

    invoice = frappe.get_doc("Invoice", invoice_number)

    if invoice.payment_status == "Paid":
        frappe.throw(_("Invoice {0} is already fully paid").format(invoice_number))

    # Tambahkan payment
    invoice.payment_amount = (invoice.payment_amount or 0) + payment_amount

    # Save (validate akan otomatis recalculate)
    invoice.save()
    frappe.db.commit()

    return {
        "message": _("Payment recorded successfully"),
        "invoice_number": invoice.name,
        "payment_amount_received": payment_amount,
        "total_payment": invoice.payment_amount,
        "outstanding_amount": invoice.outstanding_amount,
        "payment_status": invoice.payment_status
    }
