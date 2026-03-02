# ═══════════════════════════════════════════════════════════════════
# MAHAL — Module Finance (app_finance_module.py)
# Intégrez ce code dans votre app.py existant
# ═══════════════════════════════════════════════════════════════════
#
# ÉTAPES D'INTÉGRATION :
#
# ÉTAPE 1 — Ajoutez les fonctions ci-dessous après ensure_users_sheet()
#
# ÉTAPE 2 — Modifiez la définition des onglets admin :
#   AVANT:
#     tabs = st.tabs(["Nouvelle transaction","Recherche","Graphiques",
#                     "Catalogue des lots","Résumé par personne",
#                     "Historique des lots","Suivi des avances", utl])
#     tab1,tab2,tab3,tab4,tab5,tab6,tab7,tab8 = tabs
#
#   APRÈS:
#     tabs = st.tabs(["Nouvelle transaction","Recherche","Graphiques",
#                     "Catalogue des lots","Résumé par personne",
#                     "Historique des lots","Suivi des avances",
#                     "💰 Finance", utl])
#     tab1,tab2,tab3,tab4,tab5,tab6,tab7,tab_fin,tab8 = tabs
#
# ÉTAPE 3 — Ajoutez ce bloc après "with tab7:" et avant "with tab8:":
#
#     with tab_fin:
#         st.markdown('<div class="page-title" style="font-size:2rem">Finance</div>', unsafe_allow_html=True)
#         st.markdown('<div class="page-subtitle">Dette financière · Dette fournisseur · Caisse · Encaissement</div>', unsafe_allow_html=True)
#         render_finance_tab(lots_existants)
#
# ─────────────────────────────────────────────────────────────────────────────
# CODE À AJOUTER (copier-coller après ensure_users_sheet)
# ─────────────────────────────────────────────────────────────────────────────



def ensure_finance_sheets():
    """Crée les 4 feuilles Finance si elles n\'existent pas encore."""
    sh = get_client().open_by_key(SPREADSHEET_ID)
    sheets_config = {
        "Dette financiere": ["Date","Creancier","Type de dette","Montant initial (MAD)",
                             "Montant rembourse (MAD)","Taux interet (%)","Date echeance","Statut","Remarque"],
        "Dette fournisseur": ["Date","Fournisseur","Description","Lot","Montant du (MAD)",
                              "Montant paye (MAD)","Date echeance","Statut","Remarque"],
        "Caisse": ["Date","Type operation","Categorie","Description",
                   "Montant (MAD)","Mode","Lot","Remarque"],
        "Encaissement": ["Date","Payeur","Lot","Description","Montant (MAD)",
                         "Mode de paiement","Type encaissement","Statut","Remarque"],
    }
    for sname, headers in sheets_config.items():
        try:
            sh.worksheet(sname)
        except gspread.WorksheetNotFound:
            ws = sh.add_worksheet(sname, rows=1000, cols=len(headers))
            ws.update([headers])



# ─── CSS for Finance KPIs ─────────────────────────────────────────────────────
# (injected into st.markdown CSS block in real integration)

def _fin_load(sname, cols):
    try:
        df = load_sheet(sname)
        if df.empty:
            return pd.DataFrame(columns=cols)
        for c in cols:
            if c not in df.columns:
                df[c] = ""
        return df
    except Exception:
        return pd.DataFrame(columns=cols)


def render_finance_tab(lots_list):
    """Render the complete Finance tab (admin only)."""
    try:
        ensure_finance_sheets()
    except Exception:
        pass

    DF_COLS = {
        "Dette financiere":  ["Date","Creancier","Type de dette","Montant initial (MAD)","Montant rembourse (MAD)","Taux interet (%)","Date echeance","Statut","Remarque"],
        "Dette fournisseur": ["Date","Fournisseur","Description","Lot","Montant du (MAD)","Montant paye (MAD)","Date echeance","Statut","Remarque"],
        "Caisse":            ["Date","Type operation","Categorie","Description","Montant (MAD)","Mode","Lot","Remarque"],
        "Encaissement":      ["Date","Payeur","Lot","Description","Montant (MAD)","Mode de paiement","Type encaissement","Statut","Remarque"],
    }

    df_df  = _fin_load("Dette financiere",  DF_COLS["Dette financiere"])
    df_dfo = _fin_load("Dette fournisseur", DF_COLS["Dette fournisseur"])
    df_ca  = _fin_load("Caisse",            DF_COLS["Caisse"])
    df_enc = _fin_load("Encaissement",      DF_COLS["Encaissement"])

    df_df  = to_numeric(df_df,  ["Montant initial (MAD)","Montant rembourse (MAD)","Taux interet (%)"])
    df_dfo = to_numeric(df_dfo, ["Montant du (MAD)","Montant paye (MAD)"])
    df_ca  = to_numeric(df_ca,  ["Montant (MAD)"])
    df_enc = to_numeric(df_enc, ["Montant (MAD)"])

    # Global KPIs
    kpi_dette_fin  = (df_df["Montant initial (MAD)"]  - df_df["Montant rembourse (MAD)"]).clip(lower=0).sum() if not df_df.empty else 0
    kpi_dette_four = (df_dfo["Montant du (MAD)"] - df_dfo["Montant paye (MAD)"]).clip(lower=0).sum()  if not df_dfo.empty else 0
    kpi_ca_in  = df_ca[df_ca["Type operation"]=="ENTREE"]["Montant (MAD)"].sum() if not df_ca.empty else 0
    kpi_ca_out = df_ca[df_ca["Type operation"]=="SORTIE"]["Montant (MAD)"].sum() if not df_ca.empty else 0
    kpi_solde  = kpi_ca_in - kpi_ca_out
    kpi_enc    = df_enc["Montant (MAD)"].sum() if not df_enc.empty else 0

    col_sol = "#2D7A3A" if kpi_solde >= 0 else "#B03A2E"

    st.markdown(f"""
    <div style="display:flex;gap:0.8rem;flex-wrap:wrap;margin-bottom:1.5rem">
      <div style="background:#FFFFFF;border:1px solid #E8E5DE;border-radius:10px;padding:1rem 1.3rem;flex:1;min-width:140px">
        <div style="font-size:0.68rem;font-weight:500;text-transform:uppercase;letter-spacing:0.07em;color:#AAA;margin-bottom:0.4rem">Dette financiere restante</div>
        <div style="font-family:\'DM Serif Display\',serif;font-size:1.4rem;color:#B03A2E">{kpi_dette_fin:,.0f} <small style="opacity:.5;font-size:0.8rem">MAD</small></div>
      </div>
      <div style="background:#FFFFFF;border:1px solid #E8E5DE;border-radius:10px;padding:1rem 1.3rem;flex:1;min-width:140px">
        <div style="font-size:0.68rem;font-weight:500;text-transform:uppercase;letter-spacing:0.07em;color:#AAA;margin-bottom:0.4rem">Dette fournisseur restante</div>
        <div style="font-family:\'DM Serif Display\',serif;font-size:1.4rem;color:#7A4100">{kpi_dette_four:,.0f} <small style="opacity:.5;font-size:0.8rem">MAD</small></div>
      </div>
      <div style="background:#FFFFFF;border:1px solid #E8E5DE;border-radius:10px;padding:1rem 1.3rem;flex:1;min-width:140px">
        <div style="font-size:0.68rem;font-weight:500;text-transform:uppercase;letter-spacing:0.07em;color:#AAA;margin-bottom:0.4rem">Solde caisse</div>
        <div style="font-family:\'DM Serif Display\',serif;font-size:1.4rem;color:{col_sol}">{kpi_solde:+,.0f} <small style="opacity:.5;font-size:0.8rem">MAD</small></div>
      </div>
      <div style="background:#FFFFFF;border:1px solid #E8E5DE;border-radius:10px;padding:1rem 1.3rem;flex:1;min-width:140px">
        <div style="font-size:0.68rem;font-weight:500;text-transform:uppercase;letter-spacing:0.07em;color:#AAA;margin-bottom:0.4rem">Total encaisse</div>
        <div style="font-family:\'DM Serif Display\',serif;font-size:1.4rem;color:#1565C0">{kpi_enc:,.0f} <small style="opacity:.5;font-size:0.8rem">MAD</small></div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    PL = dict(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
              font=dict(family="DM Sans", color="#555", size=12),
              margin=dict(l=10, r=10, t=40, b=10))

    ftab1, ftab2, ftab3, ftab4 = st.tabs([
        "🏦 Dette financiere",
        "📦 Dette fournisseur",
        "💵 Caisse",
        "✅ Encaissement",
    ])

    # ── DETTE FINANCIERE ───────────────────────────────────────────────────────
    with ftab1:
        st.markdown(\'<div class="section-title">Dette financiere</div>\', unsafe_allow_html=True)
        st.caption("Emprunts bancaires, credits, dettes envers des personnes physiques ou morales.")

        with st.expander("➕ Ajouter une dette financiere", expanded=False):
            fc1, fc2, fc3 = st.columns(3, gap="large")
            with fc1:
                df_date   = st.date_input("Date", datetime.now(), key="df_date")
                df_crea   = st.text_input("Creancier / Banque", key="df_crea", placeholder="Ex: BMCE, Ali Hassan...")
                df_type   = st.selectbox("Type de dette", ["Emprunt bancaire","Credit fournisseur","Pret personnel","Autre"], key="df_type")
            with fc2:
                df_mi     = st.number_input("Montant initial (MAD)", min_value=0.0, step=100.0, key="df_mi")
                df_mr     = st.number_input("Montant deja rembourse (MAD)", min_value=0.0, step=100.0, key="df_mr")
                df_taux   = st.number_input("Taux d\'interet (%)", min_value=0.0, step=0.1, key="df_taux")
            with fc3:
                df_ech    = st.date_input("Date d\'echeance", key="df_ech")
                df_stat   = st.selectbox("Statut", ["En cours","Rembourse","En retard","Renegocie"], key="df_stat")
                df_rem    = st.text_input("Remarque", key="df_rem")

            if st.button("Enregistrer la dette", key="btn_df_save"):
                row = {"Date": str(df_date), "Creancier": sanitize_text(df_crea),
                       "Type de dette": df_type, "Montant initial (MAD)": df_mi,
                       "Montant rembourse (MAD)": df_mr, "Taux interet (%)": df_taux,
                       "Date echeance": str(df_ech), "Statut": df_stat,
                       "Remarque": sanitize_text(df_rem)}
                try:
                    append_row(row, "Dette financiere")
                    st.success("Dette financiere enregistree.")
                    clear_data_cache(); st.rerun()
                except Exception as e:
                    st.error(f"Erreur : {e}")

        if not df_df.empty:
            df_df_d = df_df.copy()
            df_df_d["Restant (MAD)"] = (df_df_d["Montant initial (MAD)"] - df_df_d["Montant rembourse (MAD)"]).clip(lower=0)
            sf_stat = st.selectbox("Filtrer par statut", ["Tous"] + sorted(df_df_d["Statut"].dropna().unique().tolist()), key="sf_dfstat")
            if sf_stat != "Tous": df_df_d = df_df_d[df_df_d["Statut"]==sf_stat]
            st.markdown(f\'<div class="info-count">{len(df_df_d)} dette(s)</div>\', unsafe_allow_html=True)
            st.dataframe(df_df_d, hide_index=True, use_container_width=True)

            if len(df_df_d) > 1:
                fig = go.Figure()
                fig.add_trace(go.Bar(name="Initial", x=df_df_d["Creancier"], y=df_df_d["Montant initial (MAD)"], marker_color="#E8B4B0"))
                fig.add_trace(go.Bar(name="Rembourse", x=df_df_d["Creancier"], y=df_df_d["Montant rembourse (MAD)"], marker_color="#2D7A3A"))
                fig.update_layout(**PL, barmode="overlay", legend=dict(orientation="h", y=-0.2, x=0.5, xanchor="center"))
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Aucune dette financiere enregistree.")

        st.markdown(\'<div class="section-title" style="font-size:1rem">Enregistrer un remboursement</div>\', unsafe_allow_html=True)
        if not df_df.empty:
            creas = df_df["Creancier"].dropna().unique().tolist()
            rc = st.selectbox("Creancier", ["— selectionner —"] + creas, key="rc_crea")
            if rc != "— selectionner —":
                rm = st.number_input("Montant rembourse ce jour (MAD)", min_value=0.0, step=100.0, key="rc_montant")
                if st.button("Enregistrer remboursement", key="btn_rc"):
                    df_df.loc[df_df["Creancier"]==rc, "Montant rembourse (MAD)"] += rm
                    try:
                        save_sheet(df_df, "Dette financiere")
                        st.success(f"Remboursement de {rm:,.0f} MAD enregistre.")
                        clear_data_cache(); st.rerun()
                    except Exception as e:
                        st.error(f"Erreur : {e}")

    # ── DETTE FOURNISSEUR ──────────────────────────────────────────────────────
    with ftab2:
        st.markdown(\'<div class="section-title">Dette fournisseur</div>\', unsafe_allow_html=True)
        st.caption("Ce que vous devez a vos fournisseurs pour des achats non encore regles.")

        with st.expander("➕ Ajouter une dette fournisseur", expanded=False):
            ff1, ff2, ff3 = st.columns(3, gap="large")
            with ff1:
                dfo_date = st.date_input("Date", datetime.now(), key="dfo_date")
                dfo_four = st.text_input("Fournisseur", key="dfo_four", placeholder="Nom du fournisseur")
                dfo_lot  = st.selectbox("Lot associe", ["—"] + lots_list, key="dfo_lot")
            with ff2:
                dfo_desc = st.text_input("Description", key="dfo_desc")
                dfo_du   = st.number_input("Montant du (MAD)", min_value=0.0, step=100.0, key="dfo_du")
                dfo_pay  = st.number_input("Deja paye (MAD)", min_value=0.0, step=100.0, key="dfo_pay")
            with ff3:
                dfo_ech  = st.date_input("Date d\'echeance", key="dfo_ech")
                dfo_stat = st.selectbox("Statut", ["A payer","Partiellement paye","Solde","En litige"], key="dfo_stat")
                dfo_rem  = st.text_input("Remarque", key="dfo_rem")

            if st.button("Enregistrer la dette fournisseur", key="btn_dfo_save"):
                row = {"Date": str(dfo_date), "Fournisseur": sanitize_text(dfo_four),
                       "Description": sanitize_text(dfo_desc), "Lot": sanitize_text(dfo_lot),
                       "Montant du (MAD)": dfo_du, "Montant paye (MAD)": dfo_pay,
                       "Date echeance": str(dfo_ech), "Statut": dfo_stat, "Remarque": sanitize_text(dfo_rem)}
                try:
                    append_row(row, "Dette fournisseur")
                    st.success("Dette fournisseur enregistree.")
                    clear_data_cache(); st.rerun()
                except Exception as e:
                    st.error(f"Erreur : {e}")

        if not df_dfo.empty:
            df_dfo_d = df_dfo.copy()
            df_dfo_d["Restant (MAD)"] = (df_dfo_d["Montant du (MAD)"] - df_dfo_d["Montant paye (MAD)"]).clip(lower=0)
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                fs = st.selectbox("Statut", ["Tous"]+sorted(df_dfo_d["Statut"].dropna().unique().tolist()), key="ffo_stat")
            with col_f2:
                fl = st.selectbox("Lot", ["Tous"]+sorted(df_dfo_d["Lot"].dropna().astype(str).unique().tolist()), key="ffo_lot")
            if fs != "Tous": df_dfo_d = df_dfo_d[df_dfo_d["Statut"]==fs]
            if fl != "Tous": df_dfo_d = df_dfo_d[df_dfo_d["Lot"]==fl]
            st.markdown(f\'<div class="info-count">{len(df_dfo_d)} dette(s) fournisseur</div>\', unsafe_allow_html=True)
            st.dataframe(df_dfo_d, hide_index=True, use_container_width=True)

            st.markdown(\'<div class="section-title" style="font-size:1rem">Resume par fournisseur</div>\', unsafe_allow_html=True)
            res = df_dfo.groupby("Fournisseur").apply(lambda x: pd.Series({
                "Total du": x["Montant du (MAD)"].sum(),
                "Total paye": x["Montant paye (MAD)"].sum(),
                "Restant": (x["Montant du (MAD)"] - x["Montant paye (MAD)"]).clip(lower=0).sum(),
            }), include_groups=False).reset_index()
            st.dataframe(res, hide_index=True, use_container_width=True)
        else:
            st.info("Aucune dette fournisseur enregistree.")

        st.markdown(\'<div class="section-title" style="font-size:1rem">Enregistrer un paiement fournisseur</div>\', unsafe_allow_html=True)
        if not df_dfo.empty:
            fours = df_dfo["Fournisseur"].dropna().unique().tolist()
            pf = st.selectbox("Fournisseur", ["— selectionner —"] + fours, key="pf_four")
            if pf != "— selectionner —":
                pm = st.number_input("Montant paye ce jour (MAD)", min_value=0.0, step=100.0, key="pf_montant")
                if st.button("Enregistrer le paiement", key="btn_pf"):
                    mask = df_dfo["Fournisseur"] == pf
                    df_dfo.loc[mask, "Montant paye (MAD)"] = df_dfo.loc[mask, "Montant paye (MAD)"] + pm
                    for i in df_dfo[mask].index:
                        r = df_dfo.at[i,"Montant du (MAD)"] - df_dfo.at[i,"Montant paye (MAD)"]
                        if r <= 0: df_dfo.at[i,"Statut"] = "Solde"
                        elif df_dfo.at[i,"Montant paye (MAD)"] > 0: df_dfo.at[i,"Statut"] = "Partiellement paye"
                    try:
                        save_sheet(df_dfo, "Dette fournisseur")
                        st.success(f"Paiement de {pm:,.0f} MAD enregistre.")
                        clear_data_cache(); st.rerun()
                    except Exception as e:
                        st.error(f"Erreur : {e}")

    # ── CAISSE ─────────────────────────────────────────────────────────────────
    with ftab3:
        st.markdown(\'<div class="section-title">Caisse</div>\', unsafe_allow_html=True)
        st.caption("Suivi de toutes les entrees et sorties d\'argent en caisse.")

        c_in  = df_ca[df_ca["Type operation"]=="ENTREE"]["Montant (MAD)"].sum() if not df_ca.empty else 0
        c_out = df_ca[df_ca["Type operation"]=="SORTIE"]["Montant (MAD)"].sum() if not df_ca.empty else 0
        c_sol = c_in - c_out
        c_col = "#2D7A3A" if c_sol >= 0 else "#B03A2E"
        st.markdown(f"""
        <div style="display:flex;gap:0.8rem;flex-wrap:wrap;margin-bottom:1.5rem">
          <div style="background:#FFFFFF;border:1px solid #E8E5DE;border-radius:10px;padding:1rem 1.3rem;flex:1;min-width:140px">
            <div style="font-size:0.68rem;text-transform:uppercase;color:#AAA;margin-bottom:0.4rem">Entrees</div>
            <div style="font-family:\'DM Serif Display\',serif;font-size:1.4rem;color:#2D7A3A">{c_in:,.0f} MAD</div>
          </div>
          <div style="background:#FFFFFF;border:1px solid #E8E5DE;border-radius:10px;padding:1rem 1.3rem;flex:1;min-width:140px">
            <div style="font-size:0.68rem;text-transform:uppercase;color:#AAA;margin-bottom:0.4rem">Sorties</div>
            <div style="font-family:\'DM Serif Display\',serif;font-size:1.4rem;color:#B03A2E">{c_out:,.0f} MAD</div>
          </div>
          <div style="background:#FFFFFF;border:1px solid #E8E5DE;border-radius:10px;padding:1rem 1.3rem;flex:1;min-width:140px">
            <div style="font-size:0.68rem;text-transform:uppercase;color:#AAA;margin-bottom:0.4rem">Solde caisse</div>
            <div style="font-family:\'DM Serif Display\',serif;font-size:1.4rem;color:{c_col}">{c_sol:+,.0f} MAD</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        with st.expander("➕ Nouvelle operation de caisse", expanded=False):
            cc1, cc2, cc3 = st.columns(3, gap="large")
            with cc1:
                ca_date = st.date_input("Date", datetime.now(), key="ca_date")
                ca_type = st.selectbox("Type operation", ["ENTREE","SORTIE"], key="ca_type")
                ca_cat  = st.selectbox("Categorie", ["Vente marchandise","Achat marchandise","Loyer","Salaire",
                                                      "Transport","Frais bancaires","Remboursement dette",
                                                      "Encaissement client","Paiement fournisseur","Divers"], key="ca_cat")
            with cc2:
                ca_desc = st.text_input("Description", key="ca_desc")
                ca_mont = st.number_input("Montant (MAD)", min_value=0.0, step=10.0, key="ca_mont")
                ca_mode = st.selectbox("Mode", ["Especes","Virement","Cheque","Mobile Payment","Autre"], key="ca_mode")
            with cc3:
                ca_lot  = st.selectbox("Lot associe (optionnel)", ["—"] + lots_list, key="ca_lot")
                ca_rem  = st.text_input("Remarque", key="ca_rem")

            if st.button("Enregistrer l\'operation", key="btn_ca_save"):
                row = {"Date": str(ca_date), "Type operation": ca_type, "Categorie": ca_cat,
                       "Description": sanitize_text(ca_desc), "Montant (MAD)": ca_mont,
                       "Mode": ca_mode, "Lot": sanitize_text(ca_lot), "Remarque": sanitize_text(ca_rem)}
                try:
                    append_row(row, "Caisse")
                    st.success("Operation de caisse enregistree.")
                    clear_data_cache(); st.rerun()
                except Exception as e:
                    st.error(f"Erreur : {e}")

        if not df_ca.empty:
            cc1, cc2, cc3 = st.columns(3)
            with cc1: fca_t = st.selectbox("Type", ["Tous","ENTREE","SORTIE"], key="fca_t")
            with cc2:
                cats = ["Toutes"] + sorted(df_ca["Categorie"].dropna().unique().tolist())
                fca_c = st.selectbox("Categorie", cats, key="fca_c")
            with cc3:
                lots_ca = ["Tous"] + sorted([x for x in df_ca["Lot"].dropna().astype(str).unique() if x and x != "—"])
                fca_l = st.selectbox("Lot", lots_ca, key="fca_l")

            df_ca_d = df_ca.copy()
            if fca_t != "Tous": df_ca_d = df_ca_d[df_ca_d["Type operation"]==fca_t]
            if fca_c != "Toutes": df_ca_d = df_ca_d[df_ca_d["Categorie"]==fca_c]
            if fca_l != "Tous": df_ca_d = df_ca_d[df_ca_d["Lot"]==fca_l]

            st.markdown(f\'<div class="info-count">{len(df_ca_d)} operation(s)</div>\', unsafe_allow_html=True)
            st.dataframe(df_ca_d, hide_index=True, use_container_width=True)

            st.markdown(\'<div class="section-title" style="font-size:1rem">Evolution de la caisse</div>\', unsafe_allow_html=True)
            df_ca_t = df_ca.copy()
            df_ca_t["Date"] = pd.to_datetime(df_ca_t["Date"], errors="coerce")
            df_ca_t = df_ca_t.dropna(subset=["Date"]).sort_values("Date")
            df_ca_t["Flux"] = df_ca_t.apply(lambda r: r["Montant (MAD)"] if r["Type operation"]=="ENTREE" else -r["Montant (MAD)"], axis=1)
            df_ca_t["Solde cumule"] = df_ca_t["Flux"].cumsum()
            if not df_ca_t.empty:
                fig_ca = go.Figure()
                fig_ca.add_trace(go.Scatter(x=df_ca_t["Date"], y=df_ca_t["Solde cumule"],
                    mode="lines+markers", name="Solde cumule",
                    line=dict(color="#1565C0", width=2),
                    fill="tozeroy", fillcolor="rgba(21,101,192,0.08)"))
                fig_ca.add_trace(go.Bar(x=df_ca_t["Date"], y=df_ca_t["Flux"], name="Flux",
                    marker_color=["#2D7A3A" if v >= 0 else "#B03A2E" for v in df_ca_t["Flux"]], opacity=0.5))
                fig_ca.update_layout(**PL, legend=dict(orientation="h", y=-0.2, x=0.5, xanchor="center"),
                    xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor="#EEE", tickformat=",.0f"))
                st.plotly_chart(fig_ca, use_container_width=True)

            st.markdown(\'<div class="section-title" style="font-size:1rem">Resume par categorie</div>\', unsafe_allow_html=True)
            res_ca = df_ca.groupby(["Categorie","Type operation"])["Montant (MAD)"].sum().reset_index()
            st.dataframe(res_ca, hide_index=True, use_container_width=True)
        else:
            st.info("Aucune operation de caisse enregistree.")

    # ── ENCAISSEMENT ───────────────────────────────────────────────────────────
    with ftab4:
        st.markdown(\'<div class="section-title">Encaissement</div>\', unsafe_allow_html=True)
        st.caption("Suivi de tous les paiements recus de vos clients et partenaires.")

        enc_tot  = df_enc["Montant (MAD)"].sum() if not df_enc.empty else 0
        enc_att  = df_enc[df_enc["Statut"]=="En attente"]["Montant (MAD)"].sum() if not df_enc.empty else 0
        enc_recu = df_enc[df_enc["Statut"]=="Recu"]["Montant (MAD)"].sum() if not df_enc.empty else 0

        st.markdown(f"""
        <div style="display:flex;gap:0.8rem;flex-wrap:wrap;margin-bottom:1.5rem">
          <div style="background:#FFFFFF;border:1px solid #E8E5DE;border-radius:10px;padding:1rem 1.3rem;flex:1;min-width:140px">
            <div style="font-size:0.68rem;text-transform:uppercase;color:#AAA;margin-bottom:0.4rem">Total encaisse</div>
            <div style="font-family:\'DM Serif Display\',serif;font-size:1.4rem;color:#1565C0">{enc_tot:,.0f} MAD</div>
          </div>
          <div style="background:#FFFFFF;border:1px solid #E8E5DE;border-radius:10px;padding:1rem 1.3rem;flex:1;min-width:140px">
            <div style="font-size:0.68rem;text-transform:uppercase;color:#AAA;margin-bottom:0.4rem">Confirme recu</div>
            <div style="font-family:\'DM Serif Display\',serif;font-size:1.4rem;color:#2D7A3A">{enc_recu:,.0f} MAD</div>
          </div>
          <div style="background:#FFFFFF;border:1px solid #E8E5DE;border-radius:10px;padding:1rem 1.3rem;flex:1;min-width:140px">
            <div style="font-size:0.68rem;text-transform:uppercase;color:#AAA;margin-bottom:0.4rem">En attente</div>
            <div style="font-family:\'DM Serif Display\',serif;font-size:1.4rem;color:#7A4100">{enc_att:,.0f} MAD</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        with st.expander("➕ Enregistrer un encaissement", expanded=False):
            ec1, ec2, ec3 = st.columns(3, gap="large")
            with ec1:
                en_date  = st.date_input("Date", datetime.now(), key="en_date")
                en_pay   = st.text_input("Payeur / Client", key="en_pay", placeholder="Nom du client")
                en_lot   = st.selectbox("Lot associe", ["—"] + lots_list, key="en_lot")
            with ec2:
                en_desc  = st.text_input("Description", key="en_desc")
                en_mont  = st.number_input("Montant (MAD)", min_value=0.0, step=10.0, key="en_mont")
                en_mode  = st.selectbox("Mode de paiement", ["Especes","Virement","Cheque","Mobile Payment","Carte bancaire","Autre"], key="en_mode")
            with ec3:
                en_type  = st.selectbox("Type encaissement", ["Vente marchandise","Acompte","Solde de compte","Remboursement","Location","Autre"], key="en_type")
                en_stat  = st.selectbox("Statut", ["Recu","En attente","Partiellement recu","Annule"], key="en_stat")
                en_rem   = st.text_input("Remarque", key="en_rem")

            if st.button("Enregistrer l\'encaissement", key="btn_en_save"):
                row = {"Date": str(en_date), "Payeur": sanitize_text(en_pay),
                       "Lot": sanitize_text(en_lot), "Description": sanitize_text(en_desc),
                       "Montant (MAD)": en_mont, "Mode de paiement": en_mode,
                       "Type encaissement": en_type, "Statut": en_stat, "Remarque": sanitize_text(en_rem)}
                try:
                    append_row(row, "Encaissement")
                    st.success("Encaissement enregistre.")
                    clear_data_cache(); st.rerun()
                except Exception as e:
                    st.error(f"Erreur : {e}")

        if not df_enc.empty:
            ce1, ce2, ce3 = st.columns(3)
            with ce1:
                fes = st.selectbox("Statut", ["Tous"]+sorted(df_enc["Statut"].dropna().unique().tolist()), key="fes")
            with ce2:
                lots_enc = ["Tous"]+sorted([x for x in df_enc["Lot"].dropna().astype(str).unique() if x and x!="—"])
                fel = st.selectbox("Lot", lots_enc, key="fel")
            with ce3:
                tet = ["Tous"]+sorted(df_enc["Type encaissement"].dropna().unique().tolist())
                fet = st.selectbox("Type", tet, key="fet")

            df_enc_d = df_enc.copy()
            if fes != "Tous": df_enc_d = df_enc_d[df_enc_d["Statut"]==fes]
            if fel != "Tous": df_enc_d = df_enc_d[df_enc_d["Lot"]==fel]
            if fet != "Tous": df_enc_d = df_enc_d[df_enc_d["Type encaissement"]==fet]

            st.markdown(f\'<div class="info-count">{len(df_enc_d)} encaissement(s)</div>\', unsafe_allow_html=True)
            st.dataframe(df_enc_d, hide_index=True, use_container_width=True)

            enc_lot = df_enc.groupby("Lot")["Montant (MAD)"].sum().reset_index()
            enc_lot = enc_lot[enc_lot["Lot"].astype(str) != "—"]
            if not enc_lot.empty:
                st.markdown(\'<div class="section-title" style="font-size:1rem">Encaissement par lot</div>\', unsafe_allow_html=True)
                fig_enc = go.Figure(go.Bar(x=enc_lot["Lot"], y=enc_lot["Montant (MAD)"],
                    marker_color="#1565C0", hovertemplate="%{x}<br>%{y:,.0f} MAD<extra></extra>"))
                fig_enc.update_layout(**PL, xaxis=dict(showgrid=False),
                    yaxis=dict(showgrid=True, gridcolor="#EEE", tickformat=",.0f"))
                st.plotly_chart(fig_enc, use_container_width=True)

            st.markdown(\'<div class="section-title" style="font-size:1rem">Resume par client / payeur</div>\', unsafe_allow_html=True)
            res_enc = df_enc.groupby("Payeur").agg(
                Total=("Montant (MAD)", "sum"), Nb=("Montant (MAD)", "count")
            ).reset_index().sort_values("Total", ascending=False)
            st.dataframe(res_enc, hide_index=True, use_container_width=True)
        else:
            st.info("Aucun encaissement enregistre.")
