frappe.ui.form.on('Invoice', {
    persentase_pajak: function(frm) {
        frm.trigger('calculate_totals');
    },
    calculate_totals: function(frm) {
        frm.dirty();
    }
});

frappe.ui.form.on('Invoice Item', {
    kuantitas: function(frm, cdt, cdn) {
        frm.dirty();
    },
    rate: function(frm, cdt, cdn) {
        frm.dirty();
    },
    items_remove: function(frm) {
        frm.dirty();
    }
});
