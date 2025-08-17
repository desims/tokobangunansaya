import sqlite3
import streamlit as st
from datetime import datetime
from reportlab.lib.pagesizes import A5
from reportlab.pdfgen import canvas
import os

# --- DB SETUP ---
conn = sqlite3.connect("tokobangunan.db", check_same_thread=False)
cur = conn.cursor()

# Buat tabel jika belum ada
cur.execute("""
CREATE TABLE IF NOT EXISTS barang (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kode TEXT UNIQUE,
    nama TEXT,
    satuan TEXT,
    harga_beli REAL,
    harga_jual REAL,
    stok INTEGER
)""")

cur.execute("""
CREATE TABLE IF NOT EXISTS transaksi (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tanggal TEXT,
    kode_barang TEXT,
    jumlah INTEGER,
    total REAL,
    FOREIGN KEY(kode_barang) REFERENCES barang(kode)
)""")
conn.commit()

# --- FUNCTIONS ---
def tambah_barang(kode, nama, satuan, harga_beli, harga_jual, stok):
    try:
        cur.execute("INSERT INTO barang VALUES (NULL, ?, ?, ?, ?, ?, ?)",
                    (kode, nama, satuan, harga_beli, harga_jual, stok))
        conn.commit()
        return True
    except:
        return False

def lihat_stok():
    return cur.execute("SELECT kode, nama, stok, satuan, harga_jual FROM barang").fetchall()

def jual_barang(kode, jumlah):
    cur.execute("SELECT nama, harga_jual, stok FROM barang WHERE kode=?", (kode,))
    barang = cur.fetchone()
    if not barang:
        return None, "Barang tidak ditemukan"
    nama, harga_jual, stok = barang
    if jumlah > stok:
        return None, "Stok tidak cukup"

    total = harga_jual * jumlah
    tanggal = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur.execute("INSERT INTO transaksi VALUES (NULL, ?, ?, ?, ?)",
                (tanggal, kode, jumlah, total))
    cur.execute("UPDATE barang SET stok=stok-? WHERE kode=?", (jumlah, kode))
    conn.commit()
    return {"tanggal": tanggal, "kode": kode, "nama": nama, "jumlah": jumlah, "harga": harga_jual, "total": total}, "Transaksi berhasil!"

def laporan_penjualan():
    return cur.execute("""
        SELECT tanggal, kode_barang, jumlah, total FROM transaksi ORDER BY tanggal DESC
    """).fetchall()

def laporan_harian():
    return cur.execute("""
        SELECT substr(tanggal, 1, 10) AS tgl, SUM(total) AS omzet
        FROM transaksi
        GROUP BY tgl
        ORDER BY tgl DESC
    """).fetchall()

# --- CETAK STRUK ---
def cetak_struk(data_transaksi):
    filename = f"struk_{data_transaksi['tanggal'].replace(':','-').replace(' ','_')}.pdf"
    c = canvas.Canvas(filename, pagesize=A5)
    c.setFont("Helvetica", 10)

    c.drawString(50, 380, "TOKO BANGUNAN MAKMUR JAYA")
    c.drawString(50, 365, f"Tanggal: {data_transaksi['tanggal']}")
    c.drawString(50, 350, "-"*30)
    c.drawString(50, 335, f"Barang : {data_transaksi['nama']}")
    c.drawString(50, 320, f"Kode   : {data_transaksi['kode']}")
    c.drawString(50, 305, f"Jumlah : {data_transaksi['jumlah']} x Rp {data_transaksi['harga']:,}")
    c.drawString(50, 290, "-"*30)
    c.drawString(50, 275, f"TOTAL  : Rp {data_transaksi['total']:,}")
    c.drawString(50, 260, "-"*30)
    c.drawString(50, 245, "Terima kasih sudah berbelanja!")

    c.save()
    return filename

# --- STREAMLIT APP ---
st.set_page_config(page_title="Toko Bangunan - Kasir", layout="wide")
st.title("🏗️ Sistem Toko Bangunan - Kasir dengan Struk PDF")

menu = st.sidebar.radio("Menu", ["📦 Stok Barang", "💰 Kasir", "📊 Laporan"])

# --- STOK BARANG ---
if menu == "📦 Stok Barang":
    st.header("Tambah Barang Baru")
    kode = st.text_input("Kode Barang")
    nama = st.text_input("Nama Barang")
    satuan = st.text_input("Satuan (sak, kg, batang, dll)")
    harga_beli = st.number_input("Harga Beli", min_value=0)
    harga_jual = st.number_input("Harga Jual", min_value=0)
    stok = st.number_input("Stok Awal", min_value=0)

    if st.button("Tambah Barang"):
        if tambah_barang(kode, nama, satuan, harga_beli, harga_jual, stok):
            st.success("Barang berhasil ditambahkan")
        else:
            st.error("Kode barang sudah ada atau gagal disimpan")

    st.subheader("Daftar Stok Barang")
    data = lihat_stok()
    st.table(data)

# --- KASIR (PENJUALAN) ---
elif menu == "💰 Kasir":
    st.header("Transaksi Penjualan")
    data = lihat_stok()
    if data:
        barang_list = {f"{d[0]} - {d[1]} (stok: {d[2]}) Rp{d[4]:,}": d[0] for d in data}
        pilihan = st.selectbox("Pilih Barang", list(barang_list.keys()))
        jumlah = st.number_input("Jumlah", min_value=1)

        if st.button("Jual"):
            data_transaksi, result = jual_barang(barang_list[pilihan], jumlah)
            if data_transaksi:
                st.success(result)

                # Cetak struk
                filename = cetak_struk(data_transaksi)
                with open(filename, "rb") as f:
                    st.download_button("🧾 Download Struk (PDF)", f, file_name=filename)
            else:
                st.error(result)
    else:
        st.warning("Belum ada data barang. Tambahkan dulu di menu Stok.")

# --- LAPORAN ---
elif menu == "📊 Laporan":
    st.header("Laporan Penjualan")
    data = laporan_penjualan()
    st.subheader("Detail Transaksi")
    st.table(data)

    st.subheader("Omzet Harian")
    omzet = laporan_harian()
    st.table(omzet)
