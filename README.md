# Invoice App (Frappe)

Custom Frappe application untuk manajemen invoice — dibuat sebagai Technical Test PT Muat.

## Tech Stack

- **Framework**: Frappe v17
- **Database**: MariaDB
- **Environment**: Docker + VS Code Dev Containers
- **OS**: Windows 11

---

## Setup & Installation

### Prerequisites

| Tool | Link |
|------|------|
| Docker Desktop | https://www.docker.com/products/docker-desktop/ |
| Git | https://git-scm.com/downloads |
| VS Code | https://code.visualstudio.com/ |
| Dev Containers Extension | Install dari VS Code Extensions |

### Langkah Instalasi

1. **Clone frappe_docker dan buka di VS Code:**
   ```bash
   git clone https://github.com/frappe/frappe_docker.git
   cd frappe_docker
   code .
   ```

2. **Buka dalam Dev Container:**
   - Tekan `Ctrl+Shift+P` → pilih **"Dev Containers: Reopen in Container"**
   - Tunggu hingga container selesai build

3. **Setup bench:**
   ```bash
   bench init --skip-redis-config-generation frappe-bench
   cd frappe-bench

   bench set-config -g db_host mariadb
   bench set-config -g redis_cache redis://redis-cache:6379
   bench set-config -g redis_queue redis://redis-queue:6379
   bench set-config -g redis_socketio redis://redis-socketio:6379

   bench new-site invoice.localhost \
     --mariadb-root-password 123 \
     --admin-password admin \
     --no-mariadb-socket

   bench use invoice.localhost
   ```

4. **Install Invoice App:**
   ```bash
   bench get-app https://github.com/wahidfebr/invoice_app.git
   bench --site invoice.localhost install-app invoice_app
   bench start
   ```

5. **Akses aplikasi:**
   - URL: `http://invoice.localhost:8000`
   - Login: `Administrator` / `admin`

---

## DocType Models

### Customer

- **Naming Rule**: `C-#####` (contoh: `C-00001`)
- **Fields**:

| Field | Fieldname | Type |
|-------|-----------|------|
| Nama Customer | `nama_customer` | Data (Mandatory) |
| Email | `email` | Data |
| Nomor Telepon | `nomor_telepon` | Data |
| Alamat | `alamat` | Small Text |

### Invoice

- **Naming Rule**: `INV/{customer_initials}/{yymm}/{#####}`
  - Contoh: Customer "Wahid" → `INV/W/2603/00001`
  - Contoh: Customer "Muat Logistik Indonesia" → `INV/MLI/2603/00001`
- **Fields**:

| Field | Fieldname | Type | Properties |
|-------|-----------|------|------------|
| Customer | `customer` | Link → Customer | Mandatory |
| Customer Name | `customer_name` | Data | Read Only, Fetch From customer |
| Tanggal Terbit | `tanggal_terbit` | Date | Mandatory, Default: Today |
| Items | `items` | Table → Invoice Item | |
| Total Harga Item | `total_harga_item` | Currency | Read Only |
| Persentase Pajak | `persentase_pajak` | Percent | Default: 0 |
| Grand Total | `grand_total` | Currency | Read Only |
| Outstanding Amount | `outstanding_amount` | Currency | Read Only |
| Payment Amount | `payment_amount` | Currency | Read Only |
| Payment Status | `payment_status` | Select | Read Only, Default: Unpaid |

### Invoice Item (Child Table)

| Field | Fieldname | Type | Properties |
|-------|-----------|------|------------|
| Nama Item | `nama_item` | Data | Mandatory |
| Kuantitas | `kuantitas` | Int | Mandatory, Default: 1 |
| Rate | `rate` | Currency | Mandatory |
| Harga | `harga` | Currency | Read Only |

---

## API Documentation

> **Penting:** Semua API memerlukan autentikasi. Login terlebih dahulu untuk mendapat session cookie.
>
> Untuk kemudahan testing, Postman Collection sudah disediakan di file [`Frappe Invoice App.postman_collection.json`](./Frappe%20Invoice%20App.postman_collection.json). Import file tersebut ke Postman untuk langsung mencoba semua endpoint beserta contoh response-nya.

### Login

**cURL:**

```bash
curl -X POST http://invoice.localhost:8000/api/method/login \
  -H "Content-Type: application/json" \
  -d '{"usr":"Administrator","pwd":"admin"}' \
  -c cookies.txt
```

**Postman:**

- Method: `POST`
- URL: `http://invoice.localhost:8000/api/method/login`
- Body (JSON): `{"usr":"Administrator","pwd":"admin"}`
- Postman otomatis menyimpan cookies untuk request berikutnya

---

### 1. Get Invoice

Mengambil detail invoice berdasarkan nomor invoice.

```
GET /api/method/invoice_app.api.get_invoice?invoice_number={invoice_number}
```

**cURL:**

```bash
curl -X GET "http://invoice.localhost:8000/api/method/invoice_app.api.get_invoice?invoice_number=INV/W/2603/00001" \
  -b cookies.txt
```

**Postman:**

- Method: `GET`
- URL: `http://invoice.localhost:8000/api/method/invoice_app.api.get_invoice`
- Params: `invoice_number` = `INV/W/2603/00001`

**Success Response (200):**

```json
{
  "message": {
    "name": "INV/W/2603/00001",
    "owner": "Administrator",
    "customer": "C-00001",
    "customer_name": "Wahid",
    "tanggal_terbit": "2026-03-28",
    "items": [
      {
        "nama_item": "Jasa Pengiriman",
        "kuantitas": 2,
        "rate": 50000,
        "harga": 100000
      }
    ],
    "total_harga_item": 100000,
    "persentase_pajak": 10,
    "grand_total": 110000,
    "outstanding_amount": 110000,
    "payment_amount": 0,
    "payment_status": "Unpaid"
  }
}
```

**Error Response — Invoice Not Found (404):**

```json
{
  "exc_type": "DoesNotExistError",
  "exception": "Invoice INV/X/9999/99999 not found"
}
```

---

### 2. Mark as Paid

Melakukan pembayaran terhadap invoice. Mendukung pembayaran bertahap (partial payment) dan overpayment.

```
POST /api/method/invoice_app.api.mark_as_paid
```

**cURL:**

```bash
curl -X POST http://invoice.localhost:8000/api/method/invoice_app.api.mark_as_paid \
  -H "Content-Type: application/json" \
  -d '{"invoice_number":"INV/W/2603/00001","payment_amount":50000}' \
  -b cookies.txt
```

**Postman:**

- Method: `POST`
- URL: `http://invoice.localhost:8000/api/method/invoice_app.api.mark_as_paid`
- Body (JSON):

```json
{
  "invoice_number": "INV/W/2603/00001",
  "payment_amount": 50000
}
```

**Success Response — Partial Payment (200):**

```json
{
  "message": {
    "message": "Payment recorded successfully",
    "invoice_number": "INV/W/2603/00001",
    "payment_amount_received": 50000,
    "total_payment": 50000,
    "outstanding_amount": 60000,
    "payment_status": "Partially Paid"
  }
}
```

**Success Response — Full Payment (200):**

```json
{
  "message": {
    "message": "Payment recorded successfully",
    "invoice_number": "INV/W/2603/00001",
    "payment_amount_received": 60000,
    "total_payment": 110000,
    "outstanding_amount": 0,
    "payment_status": "Paid"
  }
}
```

**Success Response — Overpayment (200):**

```json
{
    "message": {
        "message": "Payment recorded successfully",
        "invoice_number": "INV/W/2603/00002",
        "payment_amount_received": 50000,
        "total_payment": 50000,
        "outstanding_amount": -40000,
        "payment_status": "Paid"
    }
}
```

> **Note:** Outstanding amount negatif menunjukkan kelebihan bayar. Lihat [Design Decision #4](#4-overpayment-diperbolehkan) untuk penjelasan lebih lanjut.

**Error Response — Already Paid:**

```json
{
  "exc_type": "ValidationError",
  "exception": "Invoice INV/W/2603/00001 is already fully paid"
}
```

---

## Design Decisions

### 1. Custom Auto Naming (`autoname()`)

Invoice menggunakan custom `autoname()` method dengan format `INV/{initials}/{yymm}/{#####}`. Initials diambil dari huruf pertama setiap kata nama customer. Sequential number di-generate menggunakan `frappe.model.naming.getseries()` untuk memastikan uniqueness.

Contoh:
- Customer "Muat Logistik Indonesia" → `INV/MLI/2603/00001`
- Customer "Wahid" → `INV/W/2603/00001`

### 2. Server-side Business Logic

Sesuai constraint yang diberikan, **semua kalkulasi dilakukan di server (Python)**, bukan di client-side JavaScript:

- **Harga per item** = `kuantitas × rate`
- **Total Harga Item** = sum dari semua harga item
- **Grand Total** = Total Harga Item + (Total Harga Item × Persentase Pajak / 100)
- **Outstanding Amount** = Grand Total − Payment Amount
- **Payment Status** otomatis berubah berdasarkan pembayaran:
  - `Unpaid` → belum ada pembayaran
  - `Partially Paid` → sudah ada pembayaran tapi belum lunas
  - `Paid` → pembayaran sudah lunas

Payment Status otomatis berubah berdasarkan kondisi:

| Kondisi | Status |
|---------|--------|
| Grand total = 0 | `Paid` |
| Payment amount ≥ grand total | `Paid` |
| Payment amount > 0 tapi < grand total | `Partially Paid` |
| Belum ada pembayaran | `Unpaid` |

Semua kalkulasi ini dijalankan di `invoice_events.py` melalui hook `validate`, yang otomatis dipanggil setiap kali document di-save. Client script (`invoice.js`) hanya men-trigger `frm.dirty()` agar form ditandai sebagai "unsaved" dan mendorong user untuk save kembali — **tidak ada kalkulasi di client-side**.

### 3. Incremental Payment (Partial Payment)

API `mark_as_paid` mendukung **pembayaran bertahap (partial payment)**. Setiap request **menambahkan** jumlah pembayaran ke total payment yang sudah ada, bukan menggantikannya. Invoice yang sudah berstatus `Paid` tidak bisa menerima pembayaran lagi dan akan mengembalikan error.

Alur pembayaran:

```
Invoice dibuat
  └─ payment_status = "Unpaid"
  └─ outstanding_amount = grand_total

Pembayaran sebagian (30.000.000 dari 73.700.000)
  └─ payment_status = "Partially Paid"
  └─ outstanding_amount = 43.700.000

Pembayaran sisa (43.700.000)
  └─ payment_status = "Paid"
  └─ outstanding_amount = 0

Attempt bayar lagi
  └─ Error: "Invoice is already fully paid"
```

### 4. Overpayment Diperbolehkan

Sistem **sengaja memperbolehkan** pembayaran yang melebihi grand total (overpayment). Ketika overpayment terjadi, `outstanding_amount` menjadi negatif yang menunjukkan kelebihan bayar.

**Alasan**: Dalam dunia nyata, overpayment bisa terjadi karena berbagai alasan (kesalahan transfer, pembulatan, dll). Dengan mencatat seluruh pembayaran apa adanya, data tetap akurat dan kelebihan bayar bisa di-refund secara manual. Menolak pembayaran hanya karena melebihi sisa tagihan justru bisa menyulitkan proses pencatatan.

Contoh overpayment:
- Grand total: `10.000`
- Payment: `50.000`
- Outstanding: `-40.000` (negatif = kelebihan bayar)
- Status: `Paid`

### 5. Input Validation

Beberapa validasi diterapkan untuk menjaga integritas data:

| Validasi | Rule |
|----------|------|
| Invoice harus punya items | Minimal 1 item |
| Rate item | Tidak boleh negatif (≥ 0) |
| Kuantitas item | Harus lebih dari 0 (> 0) |
| Persentase pajak | Tidak boleh negatif (≥ 0) |
| Customer harus valid | Customer harus ada di database |
| Grand total = 0 | Otomatis Paid (tidak perlu bayar) |

### 6. Print Format (Jinja Template)

Menggunakan custom Jinja template print format yang menampilkan:
- **Header**: Nama Perusahaan + judul "Invoice"
- **Info**: Nomor Invoice, Nama Customer, Tanggal Terbit
- **Tabel Item**: No, Nama Item, Kuantitas, Rate, Harga
- **Summary**: Total Harga Item, Persentase Pajak, Grand Total
- **Payment Information**: Status badge berwarna (🔴 Unpaid / 🟡 Partially Paid / 🟢 Paid) + breakdown Total Dibayar & Sisa Tagihan

Format currency menggunakan `doc.get_formatted()` untuk konsistensi tampilan.

### 7. Separation of Concerns — Hooks vs Class Method

Business logic Invoice ditulis di file terpisah `invoice_events.py` (bukan di class `Invoice` pada `invoice.py`), dan didaftarkan melalui `hooks.py`. Pendekatan ini dipilih karena:
- **Modular**: Logic terpisah dari definisi DocType, lebih mudah di-maintain
- **Testable**: Fungsi-fungsi bisa di-test secara independen
- **Extensible**: Bisa menambah/menghapus hook tanpa mengubah core DocType

---

## Print Format / Screenshot

Print format tersedia dalam 4 skenario pembayaran. File PDF disertakan di repository:

| Skenario | File |
|----------|------|
| Invoice belum dibayar | [`Invoice_Unpaid.pdf`](./Invoice_Unpaid.pdf) |
| Invoice dibayar sebagian | [`Invoice_Partially_Paid.pdf`](./Invoice_Partially_Paid.pdf) |
| Invoice lunas | [`Invoice_Paid.pdf`](./Invoice_Paid.pdf) |
| Invoice dengan overpayment | [`Invoice_Paid_More_Than_Grand_Total.pdf`](./Invoice_Paid_More_Than_Grand_Total.pdf) |

---

## Project Structure

```
invoice_app/
├── Frappe Invoice App.postman_collection.json  ← Postman Collection (import untuk testing)
├── Invoice_Unpaid.pdf                          ← Print Format: Unpaid
├── Invoice_Partially_Paid.pdf                  ← Print Format: Partially Paid
├── Invoice_Paid.pdf                            ← Print Format: Paid
├── Invoice_Paid_More_Than_Grand_Total.pdf      ← Print Format: Overpayment
├── invoice_app/
│   ├── __init__.py
│   ├── api.py                                  ← API endpoints (get_invoice, mark_as_paid)
│   ├── hooks.py                                ← Event hooks registration
│   └── invoice_app/
│       ├── doctype/
│       │   ├── customer/                       ← Customer DocType
│       │   │   ├── customer.json
│       │   │   └── customer.py
│       │   ├── invoice/                        ← Invoice DocType
│       │   │   ├── invoice.json
│       │   │   ├── invoice_events.py           ← Business logic (autoname, validate, calculate)
│       │   │   └── invoice.js                  ← Client script (trigger dirty state)
│       │   └── invoice_item/                   ← Invoice Item (Child Table)
│       │       ├── invoice_item.json
│       │       └── invoice_item.py
│       └── print_format/
│           └── invoice_print/                  ← Custom Print Format (Jinja)
│               └── invoice_print.json
├── setup.py
└── README.md
```

---

## License

MIT
