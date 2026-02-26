import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go
import gspread
from google.oauth2.service_account import Credentials
import bcrypt
import time

# ─── Config ───────────────────────────────────────────────────────────────────
st.set_page_config(page_title="MAHAL — Gestion", layout="wide", initial_sidebar_state="collapsed")

SPREADSHEET_ID = "1iiBU5dxAymvo6Sxl3lXpyWLvniLMdNHHSnNDw7I7avA"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
MAX_ATTEMPTS = 5
LOCKOUT_SECONDS = 300

# ─── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Serif+Display&display=swap');

*, *::before, *::after { box-sizing: border-box; }
html, body, .stApp { background-color: #F7F6F2; color: #1C1C1C; font-family: 'DM Sans', sans-serif; }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 3rem 4rem 4rem 4rem; max-width: 1300px; }

/* CURSEUR NOIR */
input, textarea, [contenteditable] { caret-color: #1C1C1C !important; }

/* ICONE OEIL (password) → gris clair */
.stTextInput button { background: transparent !important; border: none !important; }
.stTextInput button svg { color: #C8C4BC !important; fill: #C8C4BC !important; opacity: 1 !important; }
.stTextInput button svg path { stroke: #C8C4BC !important; fill: none !important; }
.stTextInput button:hover svg { color: #999 !important; fill: #999 !important; }
.stTextInput button:hover svg path { stroke: #999 !important; }

/* AUTH */
.auth-brand { font-family: 'DM Serif Display', serif; font-size: 4rem; color: #F7F6F2; line-height: 1; letter-spacing: -0.02em; margin-bottom: 0.5rem; }
.auth-brand-sub { font-size: 0.72rem; color: #F7F6F2; letter-spacing: 0.14em; text-transform: uppercase; margin-bottom: 4rem; }
.auth-features { display: flex; flex-direction: column; gap: 1.6rem; }
.auth-feature-dot { width: 1px; height: 36px; background: rgba(247,246,242,0.18); flex-shrink: 0; margin-top: 2px; }
.auth-feature-text { font-size: 0.82rem; color: #F7F6F2; line-height: 1.5; }
.auth-form-title { font-family: 'DM Serif Display', serif; font-size: 2.2rem; color: #1C1C1C; line-height: 1.1; margin-bottom: 0.5rem; }
.auth-form-desc { font-size: 0.82rem; color: #999; line-height: 1.6; margin-bottom: 2.2rem; }
.auth-divider { display: flex; align-items: center; gap: 0.8rem; margin: 0.8rem 0; color: #CCC; font-size: 0.72rem; }
.auth-divider::before, .auth-divider::after { content: ''; flex: 1; height: 1px; background: #E0DDD5; }
.auth-switch-text { font-size: 0.76rem; color: #BBB; text-align: center; margin-top: 1.5rem; }

/* TOP BAR */
.topbar { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.3rem; }
.topbar-user { font-size: 0.8rem; color: #999; letter-spacing: 0.04em; padding-top: 0.8rem; }
.topbar-role { display: inline-block; font-size: 0.68rem; font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase; padding: 0.25rem 0.8rem; border-radius: 20px; margin-left: 0.5rem; }
.role-admin { background: #1C1C1C; color: #F7F6F2; }
.role-visiteur { background: #E8E5DE; color: #777; }

/* NOTIFICATION */
.notif-badge { display: inline-flex; align-items: center; justify-content: center; background: #E53935; color: #FFF; font-size: 0.65rem; font-weight: 700; width: 18px; height: 18px; border-radius: 50%; margin-left: 6px; vertical-align: middle; }
.notif-banner { background: #FFF3E0; border: 1px solid #FFB74D; border-radius: 8px; padding: 0.75rem 1.2rem; margin-bottom: 1rem; display: flex; align-items: center; gap: 0.8rem; font-size: 0.88rem; color: #7A4100; }
.notif-banner-dot { width: 8px; height: 8px; border-radius: 50%; background: #FFB74D; flex-shrink: 0; }

/* BADGES */
.badge-pending { display: inline-block; background: #FFF8E1; border: 1px solid #F0C040; color: #7A5C00; font-size: 0.72rem; padding: 0.2rem 0.7rem; border-radius: 20px; font-weight: 500; }
.badge-approved { background: #EEF7EE; border: 1px solid #C3DEC3; color: #2D6A2D; }
.badge-rejected { background: #FDECEA; border: 1px solid #E8B4B0; color: #7A1C1C; }

/* PAGE TITLES */
.page-title { font-family: 'DM Serif Display', serif; font-size: 2.6rem; color: #1C1C1C; margin-bottom: 0.2rem; line-height: 1.1; }
.page-subtitle { font-size: 0.85rem; color: #999; font-weight: 300; letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 2.5rem; }
.section-title { font-family: 'DM Serif Display', serif; font-size: 1.35rem; color: #1C1C1C; margin-top: 2rem; margin-bottom: 1.2rem; padding-bottom: 0.6rem; border-bottom: 1px solid #E0DDD5; }

/* METRICS */
.metric-row { display: flex; gap: 1rem; margin-bottom: 2rem; }
.metric-card { background: #FFFFFF; border: 1px solid #E8E5DE; border-radius: 10px; padding: 1.2rem 1.5rem; flex: 1; }
.metric-label { font-size: 0.72rem; font-weight: 500; text-transform: uppercase; letter-spacing: 0.07em; color: #AAA; margin-bottom: 0.5rem; }
.metric-value { font-family: 'DM Serif Display', serif; font-size: 1.55rem; color: #1C1C1C; line-height: 1; }
.metric-value.positive { color: #2D7A3A; }
.metric-value.negative { color: #B03A2E; }

/* INPUTS */
.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stDateInput > div > div > input {
    background: #F7F6F2 !important; border: 1px solid #DDDAD2 !important;
    border-radius: 8px !important; color: #1C1C1C !important;
    font-family: 'DM Sans', sans-serif !important; font-size: 0.9rem !important;
    padding: 0.55rem 0.9rem !important; -webkit-text-fill-color: #1C1C1C !important;
    caret-color: #1C1C1C !important;
}
.stTextInput > div > div > input::placeholder,
.stNumberInput > div > div > input::placeholder { color: #AAAAAA !important; -webkit-text-fill-color: #AAAAAA !important; opacity: 1 !important; }
.stTextInput > div > div > input:focus,
.stNumberInput > div > div > input:focus { border-color: #1C1C1C !important; box-shadow: none !important; }
.stTextInput label, .stNumberInput label, .stSelectbox label, .stDateInput label, .stMultiSelect label {
    font-size: 0.75rem !important; font-weight: 500 !important; letter-spacing: 0.06em !important;
    text-transform: uppercase !important; color: #999 !important; margin-bottom: 0.3rem !important;
}
.stSelectbox > div > div > div { background: #F7F6F2 !important; border: 1px solid #DDDAD2 !important; border-radius: 8px !important; font-family: 'DM Sans', sans-serif !important; font-size: 0.9rem !important; color: #1C1C1C !important; }
.stSelectbox [data-baseweb="select"] span, .stSelectbox [data-baseweb="select"] div { color: #1C1C1C !important; }
.stSelectbox svg, .stNumberInput svg, .stDateInput svg, .stMultiSelect svg { display: block !important; color: #1C1C1C !important; fill: #1C1C1C !important; }
.stSelectbox input, [data-baseweb="select"] input, [data-baseweb="combobox"] input { color: #1C1C1C !important; -webkit-text-fill-color: #1C1C1C !important; caret-color: #1C1C1C !important; }
[data-baseweb="popover"] li, [data-baseweb="menu"] li, [data-baseweb="option"] { color: #1C1C1C !important; background: #FFFFFF !important; font-family: 'DM Sans', sans-serif !important; font-size: 0.9rem !important; }
[data-baseweb="option"]:hover { background: #F0EDE5 !important; }
.stCheckbox label, .stCheckbox label p, .stCheckbox span { color: #1C1C1C !important; font-size: 0.88rem !important; }

/* BUTTONS */
.stButton > button { background: #1C1C1C !important; color: #F7F6F2 !important; border: none !important; border-radius: 8px !important; padding: 0.65rem 2.2rem !important; font-family: 'DM Sans', sans-serif !important; font-size: 0.88rem !important; font-weight: 500 !important; letter-spacing: 0.03em !important; margin-top: 1rem; transition: opacity 0.2s ease !important; }
.stButton > button:hover { opacity: 0.72 !important; }

/* ALERTS — position normale (pas de margin-top négatif) */
.stSuccess > div { background: #F0F7F0 !important; border: 1px solid #C3DEC3 !important; border-radius: 8px !important; color: #2D6A2D !important; font-size: 0.88rem !important; }

/* DATAFRAME */
.stDataFrame { border-radius: 10px !important; overflow: hidden !important; border: 1px solid #E8E5DE !important; }
.stDataFrame table { font-size: 0.88rem !important; font-family: 'DM Sans', sans-serif !important; }
.stDataFrame thead th { background: #F0EDE5 !important; color: #777 !important; font-weight: 500 !important; font-size: 0.75rem !important; letter-spacing: 0.05em !important; text-transform: uppercase !important; padding: 0.75rem 1rem !important; border-bottom: 1px solid #DDDAD2 !important; }
.stDataFrame tbody tr:nth-child(even) td { background: #FAFAF8 !important; }
.stDataFrame tbody td { padding: 0.65rem 1rem !important; border-bottom: 1px solid #F0EDE5 !important; color: #1C1C1C !important; }

/* TABS */
.stTabs [data-baseweb="tab-list"] { gap: 0; background: transparent; border-bottom: 1px solid #E0DDD5; }
.stTabs [data-baseweb="tab"] { font-family: 'DM Sans', sans-serif !important; font-size: 0.88rem !important; font-weight: 400 !important; color: #AAA !important; background: transparent !important; border: none !important; border-bottom: 2px solid transparent !important; border-radius: 0 !important; padding: 0.65rem 1.4rem !important; }
.stTabs [aria-selected="true"] { color: #1C1C1C !important; border-bottom: 2px solid #1C1C1C !important; font-weight: 500 !important; }
.stTabs [data-baseweb="tab-panel"] { padding-top: 0 !important; }
.info-count { font-size: 0.8rem; color: #999; margin-bottom: 0.8rem; }

/* USER CARD */
.user-card { background: #FFFFFF; border: 1px solid #E8E5DE; border-radius: 10px; padding: 1rem 1.2rem; margin-bottom: 0.7rem; }
.user-card-name { font-weight: 600; font-size: 0.95rem; color: #1C1C1C; }
.user-card-meta { font-size: 0.75rem; color: #AAA; margin-top: 0.2rem; }

/* BOUTONS SUGGESTION — style chip compact */
[data-testid="stHorizontalBlock"] > div [data-testid="stButton"] > button {
    background: #F0EDE5 !important; color: #555 !important;
    border: 1px solid #DDDAD2 !important; border-radius: 20px !important;
    padding: 0.2rem 0.75rem !important; font-size: 0.78rem !important;
    font-weight: 400 !important; margin-top: 0 !important;
    letter-spacing: 0 !important;
}
[data-testid="stHorizontalBlock"] > div [data-testid="stButton"] > button:hover {
    background: #E8E5DE !important; opacity: 1 !important;
}
</style>
""", unsafe_allow_html=True)

# ─── Google Sheets ─────────────────────────────────────────────────────────────
@st.cache_resource
def get_client():
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=SCOPES)
    return gspread.authorize(creds)

def load_sheet(sheet_name):
    sh = get_client().open_by_key(SPREADSHEET_ID)
    data = sh.worksheet(sheet_name).get_all_records()
    return pd.DataFrame(data) if data else pd.DataFrame()

def save_sheet(df, sheet_name):
    sh = get_client().open_by_key(SPREADSHEET_ID)
    ws = sh.worksheet(sheet_name)
    ws.clear()
    df2 = df.fillna("").astype(str)
    ws.update([df2.columns.tolist()] + df2.values.tolist())

def append_row(row_dict, sheet_name):
    sh = get_client().open_by_key(SPREADSHEET_ID)
    ws = sh.worksheet(sheet_name)
    headers = ws.row_values(1)
    ws.append_row([str(row_dict.get(h, "")) for h in headers])

def ensure_users_sheet():
    sh = get_client().open_by_key(SPREADSHEET_ID)
    try:
        sh.worksheet("Utilisateurs")
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet("Utilisateurs", rows=500, cols=12)
        ws.update([["username","password_hash","role","statut","lots_autorises","created_at","nom","prenom"]])

# ─── Auth helpers ──────────────────────────────────────────────────────────────
def hash_password(p): return bcrypt.hashpw(p.encode(), bcrypt.gensalt()).decode()
def check_password(p, h):
    try: return bcrypt.checkpw(p.encode(), h.encode())
    except: return False

def get_users() -> pd.DataFrame:
    try:
        df = load_sheet("Utilisateurs")
        if df.empty:
            df = pd.DataFrame(columns=["username","password_hash","role","statut","lots_autorises","created_at","nom","prenom"])
        for col in ["nom","prenom"]:
            if col not in df.columns: df[col] = ""
        return df
    except gspread.exceptions.WorksheetNotFound:
        ensure_users_sheet()
        return pd.DataFrame(columns=["username","password_hash","role","statut","lots_autorises","created_at","nom","prenom"])
    except Exception:
        return pd.DataFrame(columns=["username","password_hash","role","statut","lots_autorises","created_at","nom","prenom"])

def save_users(df): save_sheet(df, "Utilisateurs")

def find_user(uname):
    users = get_users()
    row = users[users["username"].str.lower() == uname.lower()]
    return None if row.empty else row.iloc[0].to_dict()

def is_locked_out(uname):
    k = f"lockout_{uname}"
    if k in st.session_state:
        elapsed = time.time() - st.session_state[k]
        if elapsed < LOCKOUT_SECONDS: return True
        del st.session_state[k]; st.session_state[f"attempts_{uname}"] = 0
    return False

def record_failed(uname):
    k = f"attempts_{uname}"
    st.session_state[k] = st.session_state.get(k, 0) + 1
    if st.session_state[k] >= MAX_ATTEMPTS: st.session_state[f"lockout_{uname}"] = time.time()

def reset_attempts(uname):
    st.session_state.pop(f"attempts_{uname}", None); st.session_state.pop(f"lockout_{uname}", None)

def admin_exists():
    u = get_users(); return not u.empty and not u[u["role"]=="admin"].empty

def count_pending():
    try: return len(get_users().query("statut == 'en_attente'"))
    except: return 0

import hashlib as _hl

SECRET_KEY = SPREADSHEET_ID[:16]

# ─── Cache serveur : persiste tant que l'app tourne (survit au refresh) ────────
@st.cache_resource
def _session_store():
    return {}

def _make_token(username):
    raw = f"{username}:{SECRET_KEY}"
    return _hl.sha256(raw.encode()).hexdigest()[:40]

def _store_session(user_dict):
    token = _make_token(user_dict["username"])
    _session_store()[token] = user_dict
    return token

def _load_session(token):
    return _session_store().get(token, None)

def _clear_session(token):
    _session_store().pop(token, None)

# ─── Session state init ────────────────────────────────────────────────────────
for k, v in [("authenticated", False), ("username", ""), ("role", ""),
              ("lots_autorises", []), ("auth_page", "login"), ("_sess_token", "")]:
    if k not in st.session_state:
        st.session_state[k] = v

# Restauration depuis l'URL au refresh
if not st.session_state.authenticated:
    token_url = st.query_params.get("t", "")
    if token_url:
        u = _load_session(token_url)
        if u:
            st.session_state.authenticated = True
            st.session_state.username = u["username"]
            st.session_state.role = u["role"]
            st.session_state.lots_autorises = u["lots_autorises"]
            st.session_state["_sess_token"] = token_url

# ─── UI helpers ───────────────────────────────────────────────────────────────
def warn(m): st.markdown(f"<div style='background:#FFF8E1;border:1px solid #F0C040;border-radius:8px;padding:0.65rem 1rem;color:#7A5C00;font-size:0.88rem;margin-bottom:0.5rem'>{m}</div>", unsafe_allow_html=True)
def err(m):  st.markdown(f"<div style='background:#FDECEA;border:1px solid #E8B4B0;border-radius:8px;padding:0.65rem 1rem;color:#7A1C1C;font-size:0.88rem;margin-bottom:0.5rem'>{m}</div>", unsafe_allow_html=True)
def ok(m):   st.markdown(f"<div style='background:#EEF7EE;border:1px solid #C3DEC3;border-radius:8px;padding:0.65rem 1rem;color:#2D6A2D;font-size:0.88rem;margin-bottom:0.5rem'>{m}</div>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# LOGIN
# ═══════════════════════════════════════════════════════════════════════════════
def page_login():
    l, r = st.columns([1.1, 1])
    with l:
        st.markdown("""<div style='background:#1C1C1C;padding:4rem;min-height:80vh;border-radius:0 12px 12px 0'>
        <div class='auth-brand'>Mahal</div></div>""", unsafe_allow_html=True)
    with r:
        st.markdown("<div class='auth-form-title'>Connexion</div><div class='auth-form-desc'>Entrez vos identifiants pour accéder à votre espace.</div>", unsafe_allow_html=True)
        uname = st.text_input("Nom d'utilisateur", key="login_user", placeholder="Votre identifiant")
        pwd   = st.text_input("Mot de passe", type="password", key="login_pass", placeholder="••••••••")
        if st.button("Se connecter", key="btn_login", use_container_width=True):
            if not uname or not pwd: err("Remplis tous les champs."); return
            if is_locked_out(uname):
                rem = int(LOCKOUT_SECONDS - (time.time() - st.session_state.get(f"lockout_{uname}", 0)))
                err(f"Compte bloqué. Réessaie dans {rem//60}m{rem%60}s."); return
            user = find_user(uname)
            if not user or not check_password(pwd, str(user["password_hash"])):
                record_failed(uname)
                att = st.session_state.get(f"attempts_{uname}", 0)
                err(f"Identifiants incorrects. {MAX_ATTEMPTS - att} tentative(s) restante(s)."); return
            if str(user["statut"]) == "en_attente": warn("Compte en attente d'approbation."); return
            if str(user["statut"]) == "rejeté": err("Compte refusé."); return
            reset_attempts(uname)
            lots_raw = str(user.get("lots_autorises",""))
            lots_list = [l.strip() for l in lots_raw.split(",") if l.strip()]
            st.session_state.authenticated = True
            st.session_state.username = str(user["username"])
            st.session_state.role = str(user["role"])
            st.session_state.lots_autorises = lots_list
            # Stocker session côté serveur et token dans l'URL
            token = _store_session({"username": str(user["username"]), "role": str(user["role"]), "lots_autorises": lots_list})
            st.session_state["_sess_token"] = token
            st.query_params["t"] = token
            st.rerun()
        st.markdown('<div class="auth-divider">ou</div>', unsafe_allow_html=True)
        if st.button("Créer un compte", key="btn_go_register", use_container_width=True):
            st.session_state.auth_page = "register"; st.rerun()
        st.markdown('<div class="auth-switch-text">Accès réservé aux membres autorisés.</div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# INSCRIPTION
# ═══════════════════════════════════════════════════════════════════════════════
def page_register():
    l, r = st.columns([1.1, 1])
    with l:
        st.markdown("""<div style='background:#1C1C1C;padding:4rem;min-height:80vh;border-radius:0 12px 12px 0'>
        <div class='auth-brand'>Mahal</div>
        <div class='auth-brand-sub'>Créer un compte</div>
        <div class='auth-features'><div class='auth-feature-item'><span class='auth-feature-dot'></span>
        <span class='auth-feature-text'>Ton compte sera examiné par l'administrateur</span></div></div>
        </div>""", unsafe_allow_html=True)
    with r:
        st.markdown("<div class='auth-form-title'>Créer un compte</div><div class='auth-form-desc'>Votre demande sera soumise à l'approbation de l'administrateur.</div>", unsafe_allow_html=True)
        rc1, rc2 = st.columns(2, gap="small")
        with rc1: prenom = st.text_input("Prénom", key="reg_prenom", placeholder="Votre prénom")
        with rc2: nom    = st.text_input("Nom", key="reg_nom", placeholder="Votre nom")
        uname = st.text_input("Nom d'utilisateur", key="reg_user", placeholder="Choisir un identifiant")
        pwd1  = st.text_input("Mot de passe", type="password", key="reg_pass", placeholder="8 car. min. avec chiffres")
        pwd2  = st.text_input("Confirmer le mot de passe", type="password", key="reg_pass2", placeholder="••••••••")
        if st.button("S'inscrire", key="btn_register", use_container_width=True):
            if not all([uname, pwd1, pwd2, prenom, nom]): err("Remplis tous les champs."); return
            if len(uname) < 3: err("Identifiant trop court (3 car. min.)."); return
            if len(pwd1) < 8: err("Mot de passe trop court (8 car. min.)."); return
            if not any(c.isdigit() for c in pwd1) or not any(c.isalpha() for c in pwd1):
                err("Le mot de passe doit contenir lettres et chiffres."); return
            if pwd1 != pwd2: err("Les mots de passe ne correspondent pas."); return
            if find_user(uname): err("Nom d'utilisateur déjà pris."); return
            is_first = not admin_exists()
            new_u = {"username": uname, "password_hash": hash_password(pwd1),
                     "role": "admin" if is_first else "visiteur",
                     "statut": "approuvé" if is_first else "en_attente",
                     "lots_autorises": "", "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                     "nom": nom.upper(), "prenom": prenom.capitalize()}
            try:
                append_row(new_u, "Utilisateurs")
                ok("Compte créé ! Tu peux te connecter." if is_first else "Inscription envoyée — en attente d'approbation.")
            except Exception as e: err(f"Erreur : {e}")
        st.markdown('<div class="auth-divider">ou</div>', unsafe_allow_html=True)
        if st.button("Retour à la connexion", key="btn_go_login", use_container_width=True):
            st.session_state.auth_page = "login"; st.rerun()

# ─── Routing ──────────────────────────────────────────────────────────────────
if not st.session_state.authenticated:
    if st.session_state.auth_page == "login": page_login()
    else: page_register()
    st.stop()

# ═══════════════════════════════════════════════════════════════════════════════
# APP PRINCIPALE
# ═══════════════════════════════════════════════════════════════════════════════
role           = st.session_state.role
username       = st.session_state.username
is_admin       = (role == "admin")
lots_autorises = st.session_state.lots_autorises

def add_quantity_column(df):
    if 'Quantité (pièces)' not in df.columns: df['Quantité (pièces)'] = 1
    return df

def to_numeric(df, cols):
    for c in cols:
        if c in df.columns: df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
    return df

def compute_resume_personne(t):
    EMPTY = pd.DataFrame(columns=['Personne','Total Achats','Total Ventes','Total Dépenses','Résultat'])
    if t.empty or 'Personne' not in t.columns: return EMPTY
    t = to_numeric(t.copy(), ['Montant (MAD)']); t = t.dropna(subset=['Personne'])
    if t.empty: return EMPTY
    g = t.groupby('Personne').apply(lambda x: pd.Series({
        'Total Achats':   x.loc[x['Type (Achat/Vente/Dépense)']=='ACHAT','Montant (MAD)'].sum(),
        'Total Ventes':   x.loc[x['Type (Achat/Vente/Dépense)']=='VENTE','Montant (MAD)'].sum(),
        'Total Dépenses': x.loc[x['Type (Achat/Vente/Dépense)']=='DÉPENSE','Montant (MAD)'].sum(),
    }), include_groups=False).reset_index()
    if g.empty or 'Total Ventes' not in g.columns: return EMPTY
    g['Résultat'] = g['Total Ventes'] - (g['Total Achats'] + g['Total Dépenses']); return g

def compute_suivi_lot(t):
    EMPTY = pd.DataFrame(columns=['Lot','Total Achats','Total Ventes','Total Dépenses','Stock Restant (pièces)','Résultat'])
    if t.empty or 'Lot' not in t.columns: return EMPTY
    t = to_numeric(t.copy(), ['Montant (MAD)','Quantité (pièces)'])
    t = t.dropna(subset=['Lot']); t = t[t['Lot'].astype(str).str.strip() != '']
    if t.empty: return EMPTY
    g = t.groupby('Lot').apply(lambda x: pd.Series({
        'Total Achats':           x.loc[x['Type (Achat/Vente/Dépense)']=='ACHAT','Montant (MAD)'].sum(),
        'Total Ventes':           x.loc[x['Type (Achat/Vente/Dépense)']=='VENTE','Montant (MAD)'].sum(),
        'Total Dépenses':         x.loc[x['Type (Achat/Vente/Dépense)']=='DÉPENSE','Montant (MAD)'].sum(),
        'Stock Restant (pièces)': (x.loc[x['Type (Achat/Vente/Dépense)']=='ACHAT','Quantité (pièces)'].sum()
                                 - x.loc[x['Type (Achat/Vente/Dépense)']=='VENTE','Quantité (pièces)'].sum()),
    }), include_groups=False).reset_index()
    if g.empty or 'Total Ventes' not in g.columns: return EMPTY
    g['Résultat'] = g['Total Ventes'] - (g['Total Achats'] + g['Total Dépenses']); return g

def compute_historique_lot(t):
    """Toutes les transactions triées par lot et date."""
    if t.empty or 'Lot' not in t.columns:
        return pd.DataFrame()
    cols = [c for c in ['Lot','Date','Type (Achat/Vente/Dépense)','Personne','Description',
                         'Montant (MAD)','Quantité (pièces)','Remarque','Statut du lot'] if c in t.columns]
    df = t[cols].copy()
    df = df[df['Lot'].astype(str).str.strip() != '']
    df = df.sort_values(['Lot','Date'], ascending=[True, False])
    return df

def compute_suivi_avances(t):
    EMPTY = pd.DataFrame(columns=['Lot','Personne','Total Avancé','Total Encaissé','Solde'])
    if t.empty or 'Lot' not in t.columns: return EMPTY
    t = to_numeric(t.copy(), ['Montant (MAD)']); t = t.dropna(subset=['Lot','Personne'])
    if t.empty: return EMPTY
    g = t.groupby(['Lot','Personne']).apply(lambda x: pd.Series({
        'Total Avancé':   x.loc[x['Type (Achat/Vente/Dépense)'].isin(['ACHAT','DÉPENSE']),'Montant (MAD)'].sum(),
        'Total Encaissé': x.loc[x['Type (Achat/Vente/Dépense)']=='VENTE','Montant (MAD)'].sum(),
    }), include_groups=False).reset_index()
    if g.empty or 'Total Encaissé' not in g.columns: return EMPTY
    g['Solde'] = g['Total Encaissé'] - g['Total Avancé']; return g

# ─── Chargement ────────────────────────────────────────────────────────────────
try:
    transactions = load_sheet("Gestion globale")
except Exception as e:
    st.error(f"Impossible de charger les données : {e}"); st.stop()

transactions = add_quantity_column(transactions)
transactions = to_numeric(transactions, ['Montant (MAD)','Quantité (pièces)'])

if not is_admin:
    if lots_autorises: transactions = transactions[transactions['Lot'].astype(str).isin(lots_autorises)]
    else: transactions = transactions.iloc[0:0]

lots_existants       = sorted([l for l in transactions['Lot'].dropna().astype(str).unique() if l.strip()])
personnes_existantes = sorted([p for p in transactions['Personne'].dropna().astype(str).unique() if p.strip()])
pending_count = count_pending() if is_admin else 0

# ─── TOP BAR ───────────────────────────────────────────────────────────────────
role_class = "role-admin" if is_admin else "role-visiteur"
role_label = "Admin" if is_admin else "Visiteur"
notif_html = f'<span class="notif-badge">{pending_count}</span>' if (is_admin and pending_count > 0) else ""

st.markdown(f"""
<div class="topbar">
  <div>
    <div class="page-title">Mahal</div>
    <div class="page-subtitle">Gestion de stock et transactions</div>
  </div>
  <div style="display:flex;align-items:center;padding-top:0.8rem">
    <span class="topbar-user">{username}</span>
    <span class="topbar-role {role_class}">{role_label}</span>{notif_html}
  </div>
</div>
""", unsafe_allow_html=True)

# Bannière notification EN HAUT
if is_admin and pending_count > 0:
    st.markdown(f"""
    <div class="notif-banner">
      <div class="notif-banner-dot"></div>
      <span><strong>{pending_count} nouvelle(s) demande(s) d'inscription</strong> en attente
      — rendez-vous dans l'onglet <strong>Utilisateurs</strong>.</span>
    </div>
    """, unsafe_allow_html=True)

dcol = st.columns([6, 1])[1]
with dcol:
    if st.button("Déconnexion", key="btn_logout"):
        _clear_session(st.session_state.get("_sess_token", ""))
        st.query_params.clear()
        for k in ["authenticated","username","role","lots_autorises","_sess_token"]: st.session_state.pop(k, None)
        st.session_state.auth_page = "login"; st.rerun()

# ─── Métriques ─────────────────────────────────────────────────────────────────
ta = transactions[transactions['Type (Achat/Vente/Dépense)']=='ACHAT']['Montant (MAD)'].sum()
tv = transactions[transactions['Type (Achat/Vente/Dépense)']=='VENTE']['Montant (MAD)'].sum()
td = transactions[transactions['Type (Achat/Vente/Dépense)']=='DÉPENSE']['Montant (MAD)'].sum()
rn = tv - (ta + td)
cr = "positive" if rn >= 0 else "negative"

st.markdown(f"""
<div class="metric-row">
  <div class="metric-card"><div class="metric-label">Total Achats</div><div class="metric-value">{ta:,.0f} <small style="opacity:.5">MAD</small></div></div>
  <div class="metric-card"><div class="metric-label">Total Ventes</div><div class="metric-value">{tv:,.0f} <small style="opacity:.5">MAD</small></div></div>
  <div class="metric-card"><div class="metric-label">Total Dépenses</div><div class="metric-value">{td:,.0f} <small style="opacity:.5">MAD</small></div></div>
  <div class="metric-card"><div class="metric-label">Résultat net</div><div class="metric-value {cr}">{rn:+,.0f} <small style="opacity:.5">MAD</small></div></div>
</div>
""", unsafe_allow_html=True)

# ─── Onglets ───────────────────────────────────────────────────────────────────
if is_admin:
    utl = f"Utilisateurs ({pending_count})" if pending_count > 0 else "Utilisateurs"
    tabs = st.tabs(["Nouvelle transaction","Recherche","Graphiques","Catalogue des lots",
                    "Résumé par personne","Historique des lots","Suivi des avances", utl])
    tab1,tab2,tab3,tab4,tab5,tab6,tab7,tab8 = tabs
else:
    tabs = st.tabs(["Mes lots","Recherche","Graphiques"])
    tab1,tab2,tab3 = tabs

# ═══════════════════════════════════════════════════════════════════════════════
# ADMIN
# ═══════════════════════════════════════════════════════════════════════════════
if is_admin:

    # ── Tab 1 : Nouvelle transaction ────────────────────────────────────────────
    with tab1:
        st.markdown('<div class="section-title">Nouvelle transaction</div>', unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3, gap="large")

        with c1:
            date = st.date_input("Date", datetime.now())
            # Personne : selectbox avec option nouvelle personne
            NOUVELLE_PERS = "＋ Nouvelle personne..."
            choix_pers = st.selectbox("Personne", [NOUVELLE_PERS] + personnes_existantes, key="sel_personne")
            if choix_pers == NOUVELLE_PERS:
                personne_val = st.text_input("Nom de la personne", key="new_personne_input", placeholder="Ex: DUPONT")
            else:
                personne_val = choix_pers
            type_trans = st.selectbox("Type de transaction", ["ACHAT","VENTE","DÉPENSE"])

        with c2:
            # Lot : selectbox avec option nouveau lot
            NOUVEAU_LOT = "＋ Nouveau lot..."
            choix_lot = st.selectbox("Lot", [NOUVEAU_LOT] + lots_existants, key="sel_lot")
            if choix_lot == NOUVEAU_LOT:
                lot_val = st.text_input("Nom du lot", key="new_lot_input", placeholder="Ex: LOT-001")
            else:
                lot_val = choix_lot
            description = st.text_input("Description")
            montant     = st.number_input("Montant (MAD)", min_value=0.0, step=0.01)

        with c3:
            quantite      = st.number_input("Quantité (pièces)", min_value=1, step=1)
            mode_paiement = st.text_input("Mode de paiement")
            statut_lot    = st.selectbox("Statut du lot", ["Actif","Fermé"])

        remarque = st.text_input("Remarque")

        if st.button("Enregistrer"):
            row = {'Date': str(date), 'Personne': personne_val.upper(),
                   'Type (Achat/Vente/Dépense)': type_trans, 'Description': description,
                   'Lot': lot_val.upper(), 'Montant (MAD)': montant,
                   'Quantité (pièces)': quantite, 'Mode de paiement': mode_paiement,
                   'Remarque': remarque, 'Statut du lot': statut_lot}
            try:
                append_row(row, "Gestion globale")
                st.success("Transaction enregistrée.")
                st.cache_resource.clear()
            except Exception as e:
                st.error(f"Erreur : {e}")

    # ── Tab 2 : Recherche ───────────────────────────────────────────────────────
    with tab2:
        st.markdown('<div class="section-title">Recherche</div>', unsafe_allow_html=True)
        cs1, cs2, cs3 = st.columns([2,1,1], gap="large")
        with cs1: query = st.text_input("Rechercher", placeholder="Nom, lot, description...")
        with cs2: filtre_type = st.selectbox("Type", ["Tous","ACHAT","VENTE","DÉPENSE"])
        with cs3:
            lots_dispo = ["Tous"] + sorted(transactions['Lot'].dropna().astype(str).unique().tolist())
            filtre_lot = st.selectbox("Lot", lots_dispo)
        df_f = transactions.copy()
        if query:
            mask = (df_f['Personne'].astype(str).str.contains(query,case=False,na=False) |
                    df_f['Lot'].astype(str).str.contains(query,case=False,na=False) |
                    df_f['Description'].astype(str).str.contains(query,case=False,na=False) |
                    df_f['Remarque'].astype(str).str.contains(query,case=False,na=False))
            df_f = df_f[mask]
        if filtre_type != "Tous": df_f = df_f[df_f['Type (Achat/Vente/Dépense)']==filtre_type]
        if filtre_lot != "Tous":  df_f = df_f[df_f['Lot']==filtre_lot]
        st.markdown(f'<div class="info-count">{len(df_f)} transaction(s)</div>', unsafe_allow_html=True)
        st.dataframe(df_f, width='stretch', hide_index=True)

    # ── Tab 3 : Graphiques ──────────────────────────────────────────────────────
    with tab3:
        st.markdown('<div class="section-title">Graphiques</div>', unsafe_allow_html=True)
        COLORS = {'ACHAT':'#5C85D6','VENTE':'#2D7A3A','DÉPENSE':'#C0864A'}
        PL = dict(paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',
                  font=dict(family='DM Sans',color='#555',size=12),margin=dict(l=10,r=10,t=40,b=10))
        gc1,gc2 = st.columns(2,gap="large")
        with gc1:
            st.markdown('<div class="section-title" style="font-size:1rem;">Répartition globale</div>', unsafe_allow_html=True)
            fig = go.Figure(go.Pie(labels=['Achats','Ventes','Dépenses'], values=[ta,tv,td], hole=0.55,
                marker=dict(colors=['#5C85D6','#2D7A3A','#C0864A'],line=dict(color='#F7F6F2',width=3)),
                hovertemplate='%{label}<br>%{value:,.0f} MAD<extra></extra>'))
            fig.update_layout(**PL,showlegend=True,legend=dict(orientation='h',y=-0.15,x=0.5,xanchor='center'))
            st.plotly_chart(fig,use_container_width=True)
        with gc2:
            st.markdown('<div class="section-title" style="font-size:1rem;">Résultat par lot</div>', unsafe_allow_html=True)
            sl = compute_suivi_lot(transactions)
            fig2 = go.Figure(go.Bar(x=sl['Lot'],y=sl['Résultat'],
                marker_color=['#2D7A3A' if v>=0 else '#B03A2E' for v in sl['Résultat']],
                hovertemplate='%{x}<br>%{y:,.0f} MAD<extra></extra>'))
            fig2.update_layout(**PL,xaxis=dict(showgrid=False),yaxis=dict(showgrid=True,gridcolor='#EEE',tickformat=',.0f'))
            st.plotly_chart(fig2,use_container_width=True)
        st.markdown('<div class="section-title" style="font-size:1rem;">Évolution dans le temps</div>', unsafe_allow_html=True)
        df_t = transactions.copy()
        df_t['Date'] = pd.to_datetime(df_t['Date'],errors='coerce')
        df_t = df_t.dropna(subset=['Date'])
        df_t['Mois'] = df_t['Date'].dt.to_period('M').astype(str)
        dp = df_t.groupby(['Mois','Type (Achat/Vente/Dépense)'])['Montant (MAD)'].sum().reset_index()
        fig3 = go.Figure()
        for tv2, col in COLORS.items():
            d = dp[dp['Type (Achat/Vente/Dépense)']==tv2]
            if not d.empty:
                fig3.add_trace(go.Scatter(x=d['Mois'],y=d['Montant (MAD)'],mode='lines+markers',name=tv2,
                    line=dict(color=col,width=2),marker=dict(size=6)))
        fig3.update_layout(**PL,xaxis=dict(showgrid=False),yaxis=dict(showgrid=True,gridcolor='#EEE',tickformat=',.0f'),
            legend=dict(orientation='h',y=-0.2,x=0.5,xanchor='center'))
        st.plotly_chart(fig3,use_container_width=True)
        st.markdown('<div class="section-title" style="font-size:1rem;">Résultat par personne</div>', unsafe_allow_html=True)
        rp = compute_resume_personne(transactions)
        fig4 = go.Figure(go.Bar(x=rp['Personne'],y=rp['Résultat'],
            marker_color=['#2D7A3A' if v>=0 else '#B03A2E' for v in rp['Résultat']],
            hovertemplate='%{x}<br>%{y:,.0f} MAD<extra></extra>'))
        fig4.update_layout(**PL,xaxis=dict(showgrid=False),yaxis=dict(showgrid=True,gridcolor='#EEE',tickformat=',.0f'))
        st.plotly_chart(fig4,use_container_width=True)

    # ── Tab 4 : Catalogue ───────────────────────────────────────────────────────
    with tab4:
        st.markdown('<div class="section-title">Catalogue des lots</div>', unsafe_allow_html=True)
        st.dataframe(compute_suivi_lot(transactions), width='stretch', hide_index=True)

    # ── Tab 5 : Résumé personne ─────────────────────────────────────────────────
    with tab5:
        st.markdown('<div class="section-title">Résumé par personne</div>', unsafe_allow_html=True)
        st.dataframe(compute_resume_personne(transactions), width='stretch', hide_index=True)

    # ── Tab 6 : Historique des lots ─────────────────────────────────────────────
    with tab6:
        st.markdown('<div class="section-title">Historique des lots</div>', unsafe_allow_html=True)
        filtre_lot_hist = st.selectbox("Filtrer par lot", ["Tous"] + lots_existants, key="hist_filtre")
        hist_df = compute_historique_lot(transactions)
        if filtre_lot_hist != "Tous":
            hist_df = hist_df[hist_df['Lot'] == filtre_lot_hist]
            t_lot = transactions[transactions['Lot'] == filtre_lot_hist]
            a_l = t_lot[t_lot['Type (Achat/Vente/Dépense)']=='ACHAT']['Montant (MAD)'].sum()
            v_l = t_lot[t_lot['Type (Achat/Vente/Dépense)']=='VENTE']['Montant (MAD)'].sum()
            d_l = t_lot[t_lot['Type (Achat/Vente/Dépense)']=='DÉPENSE']['Montant (MAD)'].sum()
            r_l = v_l - (a_l + d_l)
            cr_l = "#2D7A3A" if r_l >= 0 else "#B03A2E"
            st.markdown(f"""
            <div class="metric-row" style="margin-bottom:1rem">
              <div class="metric-card"><div class="metric-label">Achats</div><div class="metric-value">{a_l:,.0f} <small style="opacity:.5">MAD</small></div></div>
              <div class="metric-card"><div class="metric-label">Ventes</div><div class="metric-value">{v_l:,.0f} <small style="opacity:.5">MAD</small></div></div>
              <div class="metric-card"><div class="metric-label">Dépenses</div><div class="metric-value">{d_l:,.0f} <small style="opacity:.5">MAD</small></div></div>
              <div class="metric-card"><div class="metric-label">Résultat</div><div class="metric-value" style="color:{cr_l}">{r_l:+,.0f} <small style="opacity:.5">MAD</small></div></div>
            </div>
            """, unsafe_allow_html=True)
        if not hist_df.empty:
            st.markdown(f'<div class="info-count">{len(hist_df)} transaction(s)</div>', unsafe_allow_html=True)
            st.dataframe(hist_df, width='stretch', hide_index=True)
        else:
            warn("Aucune transaction pour ce lot.")

    # ── Tab 7 : Avances + Suppressions ─────────────────────────────────────────
    with tab7:
        st.markdown('<div class="section-title">Suivi des avances</div>', unsafe_allow_html=True)
        st.dataframe(compute_suivi_avances(transactions), width='stretch', hide_index=True)
        st.markdown('<div class="section-title">Supprimer des transactions</div>', unsafe_allow_html=True)
        dc1, dc2 = st.columns(2, gap="large")
        with dc1:
            st.markdown("**Supprimer toutes les transactions d'un lot**")
            lots_ex = sorted(transactions['Lot'].dropna().astype(str).unique().tolist())
            lot_sup = st.selectbox("Choisir un lot", ["— sélectionner —"]+lots_ex, key="del_lot")
            if lot_sup != "— sélectionner —":
                st.markdown(f'<div class="info-count">{len(transactions[transactions["Lot"]==lot_sup])} transaction(s)</div>', unsafe_allow_html=True)
            c_lot = st.checkbox("Je confirme la suppression du lot", key="confirm_lot")
            if st.button("Supprimer le lot", key="btn_del_lot"):
                if lot_sup == "— sélectionner —": warn("Sélectionne un lot.")
                elif not c_lot: warn("Coche la case de confirmation.")
                else:
                    transactions = transactions[transactions['Lot']!=lot_sup]
                    save_sheet(transactions,"Gestion globale"); st.success(f"Lot « {lot_sup} » supprimé."); st.cache_resource.clear()
        with dc2:
            st.markdown("**Supprimer toutes les transactions d'une personne**")
            pers_ex = sorted(transactions['Personne'].dropna().astype(str).unique().tolist())
            pers_sup = st.selectbox("Choisir une personne", ["— sélectionner —"]+pers_ex, key="del_pers")
            if pers_sup != "— sélectionner —":
                st.markdown(f'<div class="info-count">{len(transactions[transactions["Personne"]==pers_sup])} transaction(s)</div>', unsafe_allow_html=True)
            c_pers = st.checkbox("Je confirme la suppression", key="confirm_pers")
            if st.button("Supprimer la personne", key="btn_del_pers"):
                if pers_sup == "— sélectionner —": warn("Sélectionne une personne.")
                elif not c_pers: warn("Coche la case de confirmation.")
                else:
                    transactions = transactions[transactions['Personne']!=pers_sup]
                    save_sheet(transactions,"Gestion globale"); st.success(f"Personne « {pers_sup} » supprimée."); st.cache_resource.clear()

    # ── Tab 8 : Utilisateurs ────────────────────────────────────────────────────
    with tab8:
        st.markdown('<div class="section-title">Gestion des utilisateurs</div>', unsafe_allow_html=True)
        users_df = get_users()
        lots_all = sorted(transactions['Lot'].dropna().astype(str).unique().tolist())

        pending = users_df[users_df["statut"] == "en_attente"]
        if not pending.empty:
            st.markdown(f"**🔔 Demandes en attente ({len(pending)})**")
            for _, row in pending.iterrows():
                uname = row["username"]
                fn = f"{str(row.get('prenom','')).strip()} {str(row.get('nom','')).strip()}".strip() or "—"
                with st.container():
                    st.markdown(f"""<div class="user-card"><div class="user-card-name">{fn}</div>
                    <div class="user-card-meta">@{uname} · {row.get('created_at','')}</div></div>""", unsafe_allow_html=True)
                    pc1, pc2, pc3 = st.columns([3,1,1], gap="small")
                    with pc1: lots_sel = st.multiselect("Lots autorisés", options=lots_all, key=f"lots_{uname}")
                    with pc2:
                        if st.button("✓ Approuver", key=f"approve_{uname}"):
                            users_df.loc[users_df["username"]==uname,"statut"] = "approuvé"
                            users_df.loc[users_df["username"]==uname,"lots_autorises"] = ",".join(lots_sel)
                            save_users(users_df); ok(f"{uname} approuvé."); st.rerun()
                    with pc3:
                        if st.button("✗ Refuser", key=f"reject_{uname}"):
                            users_df.loc[users_df["username"]==uname,"statut"] = "rejeté"
                            save_users(users_df); warn(f"{uname} refusé."); st.rerun()
            st.markdown("---")

        st.markdown("**Tous les utilisateurs**")
        search_user = st.text_input("Rechercher un utilisateur", placeholder="Nom, prénom ou identifiant...", key="search_users")
        approved = users_df[users_df["statut"] != "en_attente"].copy()
        if search_user:
            m = (approved["username"].astype(str).str.contains(search_user,case=False,na=False) |
                 approved["nom"].astype(str).str.contains(search_user,case=False,na=False) |
                 approved["prenom"].astype(str).str.contains(search_user,case=False,na=False))
            approved = approved[m]
        st.markdown(f'<div class="info-count">{len(approved)} utilisateur(s)</div>', unsafe_allow_html=True)

        for _, row in approved.iterrows():
            uname = row["username"]
            if uname == username: continue
            fn = f"{str(row.get('prenom','')).strip()} {str(row.get('nom','')).strip()}".strip() or "—"
            with st.container():
                st.markdown(f"""<div class="user-card"><div class="user-card-name">{fn}</div>
                <div class="user-card-meta">@{uname} · {row.get('created_at','')} · {'Admin' if row['role']=='admin' else 'Visiteur'}</div>
                </div>""", unsafe_allow_html=True)
                ac1, ac2, ac3, ac4 = st.columns([1,3,1,1], gap="small")
                with ac1:
                    sb = "badge-approved" if row["statut"]=="approuvé" else "badge-rejected"
                    st.markdown(f"<span class='badge-pending {sb}'>{row['statut']}</span>", unsafe_allow_html=True)
                with ac2:
                    la = [l.strip() for l in str(row.get("lots_autorises","")).split(",") if l.strip()]
                    new_lots = st.multiselect("Lots", options=lots_all, default=la, key=f"edit_lots_{uname}")
                with ac3:
                    new_role = st.selectbox("Rôle", ["visiteur","admin"], index=0 if row["role"]=="visiteur" else 1, key=f"role_{uname}")
                with ac4:
                    if st.button("Sauvegarder", key=f"save_{uname}"):
                        users_df.loc[users_df["username"]==uname,"lots_autorises"] = ",".join(new_lots)
                        users_df.loc[users_df["username"]==uname,"role"] = new_role
                        save_users(users_df); ok(f"{uname} mis à jour."); st.rerun()
                    if st.button("Supprimer", key=f"del_{uname}"):
                        users_df = users_df[users_df["username"]!=uname]
                        save_users(users_df); ok(f"{uname} supprimé."); st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# VISITEUR
# ═══════════════════════════════════════════════════════════════════════════════
else:
    with tab1:
        st.markdown('<div class="section-title">Mes lots autorisés</div>', unsafe_allow_html=True)
        if lots_autorises: st.markdown(f'<div class="info-count">Lots visibles : {", ".join(lots_autorises)}</div>', unsafe_allow_html=True)
        else: warn("Aucun lot ne t'a été attribué. Contacte l'administrateur.")
        st.dataframe(compute_suivi_lot(transactions), width='stretch', hide_index=True)

    with tab2:
        st.markdown('<div class="section-title">Recherche</div>', unsafe_allow_html=True)
        query_v = st.text_input("Rechercher", placeholder="Description, remarque...")
        df_v = transactions.copy()
        if query_v:
            mask = (df_v['Description'].astype(str).str.contains(query_v,case=False,na=False) |
                    df_v['Remarque'].astype(str).str.contains(query_v,case=False,na=False))
            df_v = df_v[mask]
        st.markdown(f'<div class="info-count">{len(df_v)} transaction(s)</div>', unsafe_allow_html=True)
        st.dataframe(df_v, width='stretch', hide_index=True)

    with tab3:
        st.markdown('<div class="section-title">Graphiques de mes lots</div>', unsafe_allow_html=True)
        PL = dict(paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',
                  font=dict(family='DM Sans',color='#555',size=12),margin=dict(l=10,r=10,t=40,b=10))
        sl_v = compute_suivi_lot(transactions)
        if not sl_v.empty:
            fig_v = go.Figure(go.Bar(x=sl_v['Lot'],y=sl_v['Résultat'],
                marker_color=['#2D7A3A' if v>=0 else '#B03A2E' for v in sl_v['Résultat']],
                hovertemplate='%{x}<br>%{y:,.0f} MAD<extra></extra>'))
            fig_v.update_layout(**PL,xaxis=dict(showgrid=False),yaxis=dict(showgrid=True,gridcolor='#EEE',tickformat=',.0f'))
            st.plotly_chart(fig_v,use_container_width=True)
        else:
            warn("Aucune donnée à afficher.")
