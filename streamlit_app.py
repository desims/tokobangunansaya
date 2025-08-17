import streamlit as st

import sqlite3
import streamlit as st
from datetime import datetime

# --- DB SETUP ---
conn = sqlite3.connect("tokobangunan.db", check_same_thread=False)
cur = conn.cursor()

# buat tabel kalau belum ada
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
    cur.execute("SELECT harga_jual, stok FROM barang WHERE kode=?", (kode,))
    barang = cur.fetchone()
    if not barang:
        return "Barang tidak ditemukan"
    harga_jual, stok = barang
    if jumlah > stok:
        return "Stok tidak cukup"

    total = harga_jual * jumlah
    tanggal = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur.execute("INSERT INTO transaksi VALUES (NULL, ?, ?, ?, ?)",
                (tanggal, kode, jumlah, total))
    cur.execute("UPDATE barang SET stok=stok-? WHERE kode=?", (jumlah, kode))
    conn.commit()
    return f"Transaksi berhasil! Total: Rp {total}"

def laporan_penjualan():
    return cur.execute("SELECT * FROM transaksi ORDER BY tanggal DESC").fetchall()

# --- STREAMLIT APP ---
st.set_page_config(page_title="Toko Bangunan - Level 1", layout="wide")
st.title("🏗️ Sistem Toko Bangunan (Basic Level 1)")

menu = st.sidebar.radio("Menu", ["📦 Stok Barang", "💰 Penjualan", "📊 Laporan"])

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

elif menu == "💰 Penjualan":
    st.header("Transaksi Penjualan")
    data = lihat_stok()
    barang_list = {f"{d[0]} - {d[1]} (stok: {d[2]})": d[0] for d in data}

    pilihan = st.selectbox("Pilih Barang", list(barang_list.keys()))
    jumlah = st.number_input("Jumlah", min_value=1)

    if st.button("Jual"):
        result = jual_barang(barang_list[pilihan], jumlah)
        if "berhasil" in result:
            st.success(result)
        else:
            st.error(result)

elif menu == "📊 Laporan":
    st.header("Laporan Penjualan")
    data = laporan_penjualan()
    st.table(data)
