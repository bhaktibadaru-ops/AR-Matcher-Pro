import streamlit as st
import pandas as pd
import io
import re
import time

# ==========================================
# 1. PAGE CONFIG & CSS (HARUS PALING ATAS)
# ==========================================
st.set_page_config(page_title="AR Matcher Pro", page_icon="✨", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"], [class*="st-"], .stApp, p, h1, h2, h3, h4, h5, h6, span, div, input, button, label, table, th, td {
        font-family: 'Poppins', sans-serif !important;
    }
    
    .stApp {
        background-color: #f8fafc;
        background-image: radial-gradient(at 0% 0%, hsla(339, 100%, 96%, 1) 0px, transparent 40%), radial-gradient(at 100% 0%, hsla(228, 100%, 96%, 1) 0px, transparent 40%);
        background-attachment: fixed;
    }
    
    div.block-container { max-width: 1050px !important; padding-top: 2.5rem !important; margin: 0 auto !important; }
    
    .step-badge-blue { background-color: #3b82f6; color: white; width: 28px; height: 28px; border-radius: 50%; display: inline-flex; justify-content: center; align-items: center; font-weight: 500; font-size: 14px; margin-right: 12px; }
    .step-badge-gray { background-color: #cbd5e1; color: white; width: 28px; height: 28px; border-radius: 50%; display: inline-flex; justify-content: center; align-items: center; font-weight: 500; font-size: 14px; margin-right: 12px; }

    div[data-testid="stVerticalBlockBorderWrapper"] { border: none !important; background: transparent; box-shadow: none; }

    button[kind="primary"] { background-color: #3b82f6 !important; color: white !important; border-radius: 8px !important; font-weight: 500 !important; border: none !important; height: 3.2em; letter-spacing: 0.3px; }
    button[kind="primary"]:hover { background-color: #2563eb !important; }
    .stButton>button { border-radius: 8px; font-weight: 500; height: 3.2em; letter-spacing: 0.3px; }

    .glass-table { width: 100%; border-collapse: collapse; margin: 1.5rem 0; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); border: 1px solid #e2e8f0; }
    .glass-table th { background-color: #f8fafc; padding: 12px 16px; text-align: left; color: #475569; font-weight: 500; border-bottom: 1px solid #e2e8f0; }
    .glass-table td { padding: 12px 16px; color: #334155; border-bottom: 1px solid #f1f5f9; }
    .glass-table tr:hover { background-color: #f8fafc; }
    
    h1, h2, h3, .step-badge-blue, .step-badge-gray { font-weight: 600 !important; }
    
    /* Animasi Masuk */
    .fade-in { animation: fadeIn 0.8s ease-in-out; }
    @keyframes fadeIn { 0% { opacity: 0; transform: translateY(20px); } 100% { opacity: 1; transform: translateY(0); } }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. LOGIKA & FUNGSI APLIKASI
# ==========================================
def find_subset_sum(numbers, target, exclude_indices=None, timeout=5.0):
    start_time = time.time()
    target_int = int(round(target))
    nums_int = [int(round(n)) for n in numbers]
    
    parent = {0: -1}
    current_sums = {0}
    
    for i, num in enumerate(nums_int):
        if time.time() - start_time > timeout: return "TIMEOUT"
        if (exclude_indices and i in exclude_indices) or num <= 0: continue
            
        new_sums = {}
        for s in list(current_sums): 
            new_sum = s + num
            if new_sum == target_int:
                indices = [i]
                curr = s
                safe_counter = 0 
                while curr > 0 and curr in parent and safe_counter < len(nums_int):
                    idx = parent[curr]
                    if idx == -1: break
                    indices.append(idx)
                    curr -= nums_int[idx]
                    safe_counter += 1
                return sorted(indices)
            if new_sum < target_int and new_sum not in parent:
                new_sums[new_sum] = i
        
        parent.update(new_sums)
        current_sums.update(new_sums.keys())
        
    return None

def super_clean_money(x):
    if x is None: return 0.0
    s = str(x).strip()
    clean_s = re.sub(r'[^0-9]', '', s)
    try: return float(clean_s)
    except: return 0.0

@st.cache_data
def convert_df_to_csv(df):
    return df.to_csv(index=False).encode('utf-8')

# --- INISIALISASI SESSION STATE ---
if 'page' not in st.session_state: st.session_state.page = 'landing'
if 'target_locked' not in st.session_state: st.session_state.target_locked = False
if 'target_val' not in st.session_state: st.session_state.target_val = 0.0
if 'data_locked' not in st.session_state: st.session_state.data_locked = False
if 'df' not in st.session_state: st.session_state.df = None
if 'col_nominal' not in st.session_state: st.session_state.col_nominal = None

def go_to_app(): st.session_state.page = 'app'
def go_to_home(): st.session_state.page = 'landing'

def lock_target():
    val = super_clean_money(st.session_state.target_input)
    if val > 0:
        st.session_state.target_val = val
        st.session_state.target_locked = True
    else:
        st.toast("Masukkan nominal lebih dari 0", icon="❌")

def unlock_target():
    st.session_state.target_locked = False
    st.session_state.data_locked = False 
    st.session_state.res1 = None
    st.session_state.res2_auto = None
    st.session_state.show_alt = False

def lock_data(df_parsed, col_name):
    st.session_state.df = df_parsed
    st.session_state.col_nominal = col_name
    st.session_state.data_locked = True
    st.session_state.res1 = None
    st.session_state.res2_auto = None
    st.session_state.show_alt = False

def unlock_data():
    st.session_state.data_locked = False
    st.session_state.res1 = None
    st.session_state.res2_auto = None
    st.session_state.show_alt = False

# ==========================================
# 3. ROUTING (LANDING PAGE VS APP PAGE)
# ==========================================

if st.session_state.page == 'landing':
    # --- HALAMAN DEPAN (LANDING PAGE) ---
    st.markdown("""
        <div class="fade-in" style="text-align: center; padding: 4rem 1rem 2rem 1rem;">
            <div style="display: inline-block; background: #eff6ff; color: #3b82f6; padding: 6px 16px; border-radius: 20px; font-weight: 600; font-size: 0.9rem; margin-bottom: 1rem; border: 1px solid #bfdbfe;">
                🚀 Internal Tools Trijayatama
            </div>
            <h1 style="font-size: 3.5rem; color: #1e293b; margin-bottom: 0.5rem; letter-spacing: -1px;">AR Matcher <span style="color: #3b82f6;">Pro</span></h1>
            <p style="font-size: 1.2rem; color: #64748b; max-width: 600px; margin: 0 auto 3rem auto; font-weight: 400;">
                Otomatiskan pencocokan data mutasi dengan invoice dalam hitungan detik. Selamat tinggal kalkulator manual!
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    _, col_btn, _ = st.columns([1, 1, 1])
    with col_btn:
        st.button("Mulai Recon Sekarang →", type="primary", use_container_width=True, on_click=go_to_app)
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Fitur-fitur
    f1, f2, f3 = st.columns(3)
    with f1:
        st.markdown("""
        <div style="background: white; padding: 2rem; border-radius: 16px; border: 1px solid #e2e8f0; text-align: center; height: 100%;">
            <div style="font-size: 2.5rem; margin-bottom: 1rem;">⚡</div>
            <h3 style="color: #1e293b; font-size: 1.1rem; margin-bottom: 0.5rem;">Super Cepat</h3>
            <p style="color: #64748b; font-size: 0.9rem;">Algoritma pintar yang memproses puluhan invoice dalam sepersekian detik.</p>
        </div>""", unsafe_allow_html=True)
    with f2:
        st.markdown("""
        <div style="background: white; padding: 2rem; border-radius: 16px; border: 1px solid #e2e8f0; text-align: center; height: 100%;">
            <div style="font-size: 2.5rem; margin-bottom: 1rem;">🎯</div>
            <h3 style="color: #1e293b; font-size: 1.1rem; margin-bottom: 0.5rem;">Akurasi Presisi</h3>
            <p style="color: #64748b; font-size: 0.9rem;">Menemukan kombinasi angka secara mutlak tanpa ada kemungkinan selisih.</p>
        </div>""", unsafe_allow_html=True)
    with f3:
        st.markdown("""
        <div style="background: white; padding: 2rem; border-radius: 16px; border: 1px solid #e2e8f0; text-align: center; height: 100%;">
            <div style="font-size: 2.5rem; margin-bottom: 1rem;">🔒</div>
            <h3 style="color: #1e293b; font-size: 1.1rem; margin-bottom: 0.5rem;">Aman & Privat</h3>
            <p style="color: #64748b; font-size: 0.9rem;">Data diproses sementara di memori dan tidak pernah disimpan ke server manapun.</p>
        </div>""", unsafe_allow_html=True)

    st.markdown("""
        <div style="text-align: center; margin-top: 80px; padding: 25px; color: #94a3b8; font-size: 0.95rem; border-top: 1px solid rgba(226, 232, 240, 0.6); font-weight: 500;">
            Crafted with 💡 by <b style="color: #64748b;">Bhakti</b> for <b style="color: #64748b;">Trijayatama</b>
        </div>
    """, unsafe_allow_html=True)

elif st.session_state.page == 'app':
    # --- HALAMAN APLIKASI UTAMA (APP PAGE) ---
    st.markdown("""
        <div class="fade-in" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2.5rem; flex-wrap: wrap; gap: 15px;">
            <div>
                <h1 style='color: #1e293b; font-size: 2.2rem; margin-bottom: 0; letter-spacing: -0.5px;'>✨ AR Matcher Pro</h1>
                <p style='color: #64748b; font-size: 1rem; margin-top: 5px; margin-bottom: 0; font-weight: 500;'>Bikin proses recon invoice lo secepat kilat. Tinggal sat-set, beres! 🚀</p>
            </div>
            <div style="display: flex; gap: 15px; align-items: center;">
                <div style="text-align: right; background: rgba(255, 255, 255, 0.7); backdrop-filter: blur(10px); padding: 10px 18px; border-radius: 12px; border: 1px solid #e2e8f0; box-shadow: 0 4px 15px rgba(0,0,0,0.02); font-size: 0.85rem; color: #64748b;">
                    <span style="font-weight: 400;">Crafted with 💡 by</span> <b style="color: #3b82f6; font-size: 0.9rem;">Bhakti</b><br>
                    <span style="font-weight: 400;">for</span> <b style="color: #1e293b; font-size: 0.9rem;">Trijayatama</b>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    st.button("← Kembali ke Beranda", on_click=go_to_home)
    st.markdown("<br>", unsafe_allow_html=True)

    col_left, col_right = st.columns([1, 1.2], gap="large")

    # ----------------- STEP 1: TARGET NOMINAL -----------------
    with col_left:
        if not st.session_state.target_locked:
            st.markdown("""<div style="background: #f0f6ff; border: 2px solid #8baef5; border-radius: 12px; padding: 1.5rem; margin-bottom: 1rem;"><div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;"><div style="display: flex; align-items: center; font-size: 1.2rem; font-weight: 600; color: #1e293b; letter-spacing: -0.3px;"><span class="step-badge-blue">1</span> Set Target Nominal</div><div style="color: #10b981; font-size: 1.2rem;">✅</div></div><div style="color: #64748b; font-size: 0.95rem; margin-bottom: 1rem; padding-left: 40px; font-weight: 400;">Masukkan total transfer masuk untuk mulai</div></div>""", unsafe_allow_html=True)
            st.text_input("Nominal", value=str(int(st.session_state.target_val)) if st.session_state.target_val > 0 else "", key="target_input", placeholder="Contoh: 150000", label_visibility="collapsed")
            st.button("Masukkan nominal & Lanjut", type="primary", use_container_width=True, on_click=lock_target)
            
            st.markdown("""<div style="text-align: center; color: #cbd5e1; margin: 10px 0;">👇</div><div style="background-color: rgba(248, 250, 252, 0.6); border: 1px solid #e2e8f0; border-radius: 12px; padding: 1.2rem; display: flex; align-items: center;"><span class="step-badge-gray">2</span><div><div style="font-weight: 600; color: #64748b; font-size: 1.1rem; letter-spacing: -0.3px;">Step 2. Masukkan Data Invoice</div><div style="font-size: 0.85rem; color: #94a3b8; margin-top: 4px; font-weight: 400;">🔒 Lanjut setelah target nominal ditentukan</div></div></div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"""<div style="background: #f0f6ff; border: 2px solid #8baef5; border-radius: 12px; padding: 1.5rem; margin-bottom: 1rem;"><div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;"><div style="display: flex; align-items: center; font-size: 1.2rem; font-weight: 600; color: #1e293b; letter-spacing: -0.3px;"><span class="step-badge-blue">1</span> Set Target Nominal</div><div style="color: #10b981; font-size: 1.2rem;">✅</div></div><div style="color: #64748b; font-size: 0.95rem; margin-bottom: 1.5rem; padding-left: 40px; font-weight: 400;">Masukkan total transfer masuk untuk mulai</div><div style="background: white; border: 1px solid #10b981; border-radius: 8px; padding: 0.8rem 1rem; display: flex; justify-content: space-between; align-items: center;"><div style="font-weight: 500; color: #1e293b; font-size: 1.1rem;">Rp. <span style="margin-left: 8px;">{int(st.session_state.target_val):,}</span></div><div style="color: #10b981;">🔒</div></div></div>""", unsafe_allow_html=True)
            st.button("Ubah Nominal Target 🔓", use_container_width=True, on_click=unlock_target)

    # ----------------- STEP 2: DATA INVOICE -----------------
    with col_right:
        if not st.session_state.target_locked:
            st.markdown("""<div style="background: rgba(241, 245, 249, 0.4); border: 1px solid #e2e8f0; border-radius: 16px; padding: 2.5rem; opacity: 0.6; pointer-events: none;"><div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;"><div style="display: flex; align-items: center; font-size: 1.2rem; font-weight: 600; color: #64748b; letter-spacing: -0.3px;"><span class="step-badge-gray">2</span> Masukkan Data Invoice</div><div style="color: #94a3b8; font-size: 1.2rem;">🔒</div></div><div style="color: #94a3b8; font-size: 0.95rem; margin-bottom: 2rem; padding-left: 40px; font-weight: 400;">🔒 Lanjut setelah target nominal ditentukan</div><div style="background: white; border: 1px solid #e2e8f0; border-radius: 12px; padding: 1.5rem;"><div style="margin-bottom: 1rem; color: #64748b; font-weight: 500; display: flex; gap: 20px;"><div>🟩 Paste Data</div><div>📁 Upload XLSX</div></div><div style="background: #f8fafc; border: 1px dashed #cbd5e1; border-radius: 8px; padding: 1rem; color: #94a3b8; font-family: monospace; font-size: 0.9rem; min-height: 120px;">Paste data tabel dari Excel ke sini...</div></div></div>""", unsafe_allow_html=True)
        
        elif st.session_state.target_locked and not st.session_state.data_locked:
            st.markdown("""<div style="background: white; border: 1px solid #e2e8f0; border-radius: 16px; padding: 2rem; box-shadow: 0 10px 25px -5px rgba(0,0,0,0.05); margin-bottom: 1rem;"><div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;"><div style="display: flex; align-items: center; font-size: 1.2rem; font-weight: 600; color: #1e293b; letter-spacing: -0.3px;"><span class="step-badge-blue">2</span> Masukkan Data Invoice</div><div style="color: #10b981; font-size: 1.2rem;">🔓</div></div><div style="color: #64748b; font-size: 0.95rem; margin-bottom: 1rem; padding-left: 40px; font-weight: 400;">Pilih metode input & tentukan kolom nominal:</div></div>""", unsafe_allow_html=True)
            
            with st.container(border=True):
                input_mode = st.radio("Pilih sumber data:", ("🟩 Paste Data", "📁 Upload XLSX"), horizontal=True, label_visibility="collapsed")
                st.markdown("<br>", unsafe_allow_html=True)
                
                df_temp = None
                if input_mode == "📁 Upload XLSX":
                    uploaded_file = st.file_uploader("Tarik file Excel ke sini", type=["xlsx", "csv"])
                    if uploaded_file:
                        df_temp = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('xlsx') else pd.read_csv(uploaded_file)
                else:
                    paste_data = st.text_area("Paste data tabel dari Excel ke kotak di bawah:", height=130, placeholder="INV001   150000\nINV002   200000")
                    if paste_data:
                        try:
                            df_temp = pd.read_csv(io.StringIO(paste_data), sep='\t', header=None)
                            if len(df_temp.columns) < 2:
                                df_temp = pd.read_csv(io.StringIO(paste_data), sep=r'\s{2,}', header=None, engine='python')
                            df_temp.columns = [f"Kolom_{i+1}" for i in range(len(df_temp.columns))]
                        except: 
                            st.error("Format data gagal dibaca. Pastikan paste data dari tabel.")
                
                if df_temp is not None and not df_temp.empty:
                    st.success(f"✅ Berhasil membaca **{len(df_temp)} baris** data.")
                    selected_col = st.selectbox("👉 Pilih Kolom yang isinya Nominal Uang:", df_temp.columns, index=len(df_temp.columns)-1)
                    
                    if st.button("Kunci Data & Lanjut", type="primary", use_container_width=True):
                        lock_data(df_temp, selected_col)
                        st.rerun()
                        
        elif st.session_state.target_locked and st.session_state.data_locked:
            st.markdown(f"""<div style="background: #f0f6ff; border: 2px solid #8baef5; border-radius: 12px; padding: 1.5rem; margin-bottom: 1rem;"><div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;"><div style="display: flex; align-items: center; font-size: 1.2rem; font-weight: 600; color: #1e293b; letter-spacing: -0.3px;"><span class="step-badge-blue">2</span> Masukkan Data Invoice</div><div style="color: #10b981; font-size: 1.2rem;">✅</div></div><div style="color: #64748b; font-size: 0.95rem; margin-bottom: 1.5rem; padding-left: 40px; font-weight: 400;">Data lo udah aman dan siap diproses</div><div style="background: white; border: 1px solid #10b981; border-radius: 8px; padding: 0.8rem 1rem; display: flex; justify-content: space-between; align-items: center;"><div style="font-weight: 500; color: #1e293b; font-size: 1rem;">📄 {len(st.session_state.df)} Baris Data Tersimpan</div><div style="color: #10b981;">🔒</div></div></div>""", unsafe_allow_html=True)
            st.button("Ubah Data Input 🔓", use_container_width=True, on_click=unlock_data)

    # ----------------- STEP 3: EKSEKUSI PENCARIAN -----------------
    if st.session_state.target_locked and st.session_state.data_locked and st.session_state.df is not None:
        st.markdown("---")
        
        _, col_btn, _ = st.columns([1, 2, 1])
        with col_btn:
            st.markdown("<h3 style='text-align: center; letter-spacing: -0.5px;'>❸ Siap Mencocokkan Data</h3>", unsafe_allow_html=True)
            btn_utama = st.button("🚀 CARI KOMBINASI SEKARANG", type="primary", use_container_width=True)

        if btn_utama:
            data_list = st.session_state.df[st.session_state.col_nominal].apply(super_clean_money).tolist()
            with st.spinner("Mencari kombinasi utama & memindai alternatif... ☕"):
                res1 = find_subset_sum(data_list, st.session_state.target_val, timeout=5.0)
                st.session_state['res1'] = res1
                
                res2_auto = None
                if res1 and res1 != "TIMEOUT" and len(res1) > 0:
                    exclude = {res1[0]} 
                    res2_auto = find_subset_sum(data_list, st.session_state.target_val, exclude_indices=exclude, timeout=2.0)
                
                st.session_state['res2_auto'] = res2_auto
                st.session_state['show_alt'] = False
            
            if res1 and res1 != "TIMEOUT":
                st.balloons()

        # --- TAMPILAN HASIL OPSI 1 ---
        if st.session_state.get('res1'):
            if st.session_state['res1'] == "TIMEOUT":
                st.error("⏳ Pencarian terlalu lama (Timeout). Data terlalu banyak atau tidak ada kecocokan pas.")
            else:
                st.markdown("<br>", unsafe_allow_html=True)
                
                auto_res = st.session_state.get('res2_auto')
                if auto_res and auto_res != "TIMEOUT":
                    st.warning("⚠️ **PERHATIAN: Ditemukan Kombinasi Alternatif!**\nSistem mendeteksi ada kumpulan invoice lain yang totalnya juga sama persis. Harap cek Opsi Alternatif di bawah untuk memastikan mana yang benar.")
                elif auto_res is None:
                    st.success("🔒 **MUTLAK: Tidak Ada Kombinasi Lain!**\nSistem menjamin ini adalah satu-satunya kombinasi invoice yang pas. Lo bisa langsung proses dengan tenang.")
                elif auto_res == "TIMEOUT":
                    st.info("⏱️ **Info:** Data terlalu kompleks untuk dipindai otomatis. Cek manual jika lo ragu.")
                    
                st.markdown("#### ✅ OPSI #1 DITEMUKAN")
                
                df_res1 = st.session_state.df.iloc[st.session_state['res1']].copy()
                df_display1 = df_res1.copy()
                df_display1[st.session_state.col_nominal] = df_display1[st.session_state.col_nominal].apply(lambda x: f"Rp {super_clean_money(x):,.0f}")
                
                total_res1 = df_res1[st.session_state.col_nominal].apply(super_clean_money).sum()
                selisih1 = st.session_state.target_val - total_res1
                
                c1, c2, c3 = st.columns(3)
                c1.metric("Target Dibayar", f"Rp {st.session_state.target_val:,.0f}")
                c2.metric("Total Match", f"Rp {total_res1:,.0f}", f"{len(st.session_state['res1'])} Invoice")
                c3.metric("Selisih", f"Rp {selisih1:,.0f}", delta_color="off")
                
                html_table = df_display1.to_html(index=False, classes='glass-table')
                st.markdown(html_table, unsafe_allow_html=True)
                
                csv_data = convert_df_to_csv(df_res1)
                st.download_button(label="📥 Download Hasil (CSV)", data=csv_data, file_name='AR_Match_Result.csv')
                
                if auto_res and auto_res != "TIMEOUT":
                    st.markdown("---")
                    if st.button("TAMPILKAN OPSI ALTERNATIF 🔄"):
                        st.session_state['show_alt'] = True
                elif auto_res == "TIMEOUT":
                    st.markdown("---")
                    if st.button("PAKSA CARI OPSI ALTERNATIF (Scan Mendalam) 🔄"):
                        with st.spinner("Mencari alternatif secara mendalam..."):
                            data_list = st.session_state.df[st.session_state.col_nominal].apply(super_clean_money).tolist()
                            exclude = {st.session_state['res1'][0]} 
                            deep_res = find_subset_sum(data_list, st.session_state.target_val, exclude_indices=exclude, timeout=8.0)
                            
                            if deep_res and deep_res != "TIMEOUT":
                                st.session_state['res2_auto'] = deep_res
                                st.session_state['show_alt'] = True
                            else:
                                st.error("Tidak ditemukan opsi lain atau data terlalu besar.")

        # --- TAMPILAN HASIL OPSI 2 ---
        if st.session_state.get('show_alt') and st.session_state.get('res2_auto'):
            st.markdown("<br>", unsafe_allow_html=True)
            st.warning("⚠️ **OPSI #2 (ALTERNATIF)**")
            
            df_res2 = st.session_state.df.iloc[st.session_state['res2_auto']].copy()
            df_display2 = df_res2.copy()
            df_display2[st.session_state.col_nominal] = df_display2[st.session_state.col_nominal].apply(lambda x: f"Rp {super_clean_money(x):,.0f}")
            
            total_res2 = df_res2[st.session_state.col_nominal].apply(super_clean_money).sum()
            selisih2 = st.session_state.target_val - total_res2
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Target Dibayar", f"Rp {st.session_state.target_val:,.0f}")
            c2.metric("Total Match", f"Rp {total_res2:,.0f}", f"{len(st.session_state['res2_auto'])} Invoice")
            c3.metric("Selisih", f"Rp {selisih2:,.0f}", delta_color="off")
            
            html_table2 = df_display2.to_html(index=False, classes='glass-table')
            st.markdown(html_table2, unsafe_allow_html=True)
