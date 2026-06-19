import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timezone
from supabase import create_client

# ── Configuración de página ──────────────────────────────────────────────────
st.set_page_config(
    page_title="Simulador de Ventas · Gira M19",
    page_icon="🍷",
    layout="wide",
)

# ── Supabase ─────────────────────────────────────────────────────────────────
@st.cache_resource
def get_supabase_client():
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)


@st.cache_data(ttl=300)
def fetch_productos():
    """Fetch products from Supabase database."""
    try:
        client = get_supabase_client()
        response = client.table("productos").select(
            "tipoproducto, descripcion_producto, presentacion, costo, precioventa"
        ).execute()
        if response.data:
            df = pd.DataFrame(response.data)
            # Rename columns to match expected format
            df = df.rename(columns={
                "tipoproducto": "Categoría",
                "descripcion_producto": "Descripción",
                "presentacion": "Presentación",
                "costo": "Costo",
                "precioventa": "Precio Venta",
            })
            # Calculate margin
            df["Costo"] = pd.to_numeric(df["Costo"], errors="coerce").fillna(0)
            df["Precio Venta"] = pd.to_numeric(df["Precio Venta"], errors="coerce").fillna(0)
            df["Margen"] = df["Precio Venta"] - df["Costo"]
            return df
        return pd.DataFrame(columns=["Categoría", "Descripción", "Presentación", "Costo", "Precio Venta", "Margen"])
    except Exception as e:
        st.error(f"Error al cargar productos: {e}")
        return pd.DataFrame(columns=["Categoría", "Descripción", "Presentación", "Costo", "Precio Venta", "Margen"])


df_base = fetch_productos()

# ── Cotización desde dolarapi.com ────────────────────────────────────────────
TIPOS_DOLAR = {
    "Oficial":                  "oficial",
    "Blue":                     "blue",
    "Bolsa (MEP)":              "bolsa",
    "Contado con Liquidación":  "contadoconliqui",
    "Mayorista":                "mayorista",
    "Cripto":                   "cripto",
    "Tarjeta":                  "tarjeta",
}

@st.cache_data(ttl=300)   # refresca cada 5 minutos
def fetch_cotizaciones():
    try:
        r = requests.get("https://dolarapi.com/v1/dolares", timeout=5)
        r.raise_for_status()
        return {d["casa"]: d for d in r.json()}
    except Exception:
        return {}

# ── Helpers ──────────────────────────────────────────────────────────────────
def fmt_ars(v):
    """Formato ARS: $ 1.234.567"""
    return f"$ {v:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")

def fmt_usd(v):
    """Formato USD: U$S 1.234"""
    return f"U$S {v:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")

# ── Header ───────────────────────────────────────────────────────────────────
LOGO_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 420 100" width="340" height="80">
  <!-- Wine glass -->
  <g transform="translate(10,6)">
    <!-- Bowl -->
    <path d="M18 4 Q6 22 10 38 Q14 52 30 56 Q46 52 50 38 Q54 22 42 4 Z"
          fill="#8B1A1A" opacity="0.92"/>
    <!-- Shine -->
    <ellipse cx="24" cy="20" rx="4" ry="9" fill="white" opacity="0.18" transform="rotate(-15,24,20)"/>
    <!-- Stem -->
    <rect x="28" y="56" width="4" height="22" rx="2" fill="#6B1010" opacity="0.85"/>
    <!-- Base -->
    <ellipse cx="30" cy="80" rx="16" ry="4" fill="#6B1010" opacity="0.75"/>
  </g>
  <!-- Text block -->
  <text x="78" y="46" font-family="Georgia, serif" font-size="34"
        font-weight="bold" fill="#2C0A0A" letter-spacing="1">Gira M19</text>
  <text x="80" y="68" font-family="Georgia, serif" font-size="15"
        fill="#7A2020" letter-spacing="2">Simulador de Ventas</text>
  <!-- Decorative line -->
  <line x1="78" y1="74" x2="380" y2="74" stroke="#8B1A1A" stroke-width="1.5" opacity="0.35"/>
</svg>
"""

st.markdown(LOGO_SVG, unsafe_allow_html=True)
st.markdown("Estimá cuántas unidades vas a vender de cada producto y calculá tus ganancias al instante.")
st.divider()

# ── Cotización USD ───────────────────────────────────────────────────────────
cotizaciones = fetch_cotizaciones()

col_tipo, col_val, col_btn, _ = st.columns([1.2, 1, 0.6, 2])

with col_tipo:
    tipo_label = st.selectbox(
        "💵 Tipo de dólar",
        options=list(TIPOS_DOLAR.keys()),
        index=1,   # Blue por defecto
    )

casa_key = TIPOS_DOLAR[tipo_label]
dato = cotizaciones.get(casa_key, {})
valor_api = dato.get("venta") or dato.get("compra") or 1200.0

with col_val:
    tipo_cambio = st.number_input(
        "Cotización (ARS)",
        min_value=1.0,
        value=float(valor_api),
        step=10.0,
        format="%.2f",
        help="Se carga automáticamente desde dolarapi.com. Podés editarlo manualmente.",
    )

with col_btn:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔄 Actualizar"):
        st.cache_data.clear()
        st.rerun()

# Info de última actualización
if dato.get("fechaActualizacion"):
    try:
        dt = datetime.fromisoformat(dato["fechaActualizacion"].replace("Z", "+00:00"))
        dt_local = dt.astimezone()
        st.caption(f"Fuente: dolarapi.com · Última actualización: {dt_local.strftime('%d/%m/%Y %H:%M')} hs")
    except Exception:
        st.caption("Fuente: dolarapi.com")
elif not cotizaciones:
    st.warning("⚠️ No se pudo obtener la cotización en línea. Editá el valor manualmente.")

st.divider()

# ── Tabla de productos con cantidades ────────────────────────────────────────
st.subheader("📦 Productos — Cargá las cantidades estimadas")

cantidades = {}
categorias = df_base["Categoría"].unique()

for cat in categorias:
    with st.expander(f"**{cat}**", expanded=True):
        df_cat = df_base[df_base["Categoría"] == cat].reset_index(drop=True)

        header = st.columns([2.5, 2, 1.2, 1.2, 1.3, 1])
        header[0].markdown("**Descripción**")
        header[1].markdown("**Presentación**")
        header[2].markdown("**Costo**")
        header[3].markdown("**Precio venta**")
        header[4].markdown("**Margen unit.**")
        header[5].markdown("**Cantidad**")

        for _, row in df_cat.iterrows():
            key = f"{row['Categoría']}|{row['Descripción']}|{row['Presentación']}"
            c0, c1, c2, c3, c4, c5 = st.columns([2.5, 2, 1.2, 1.2, 1.3, 1])
            c0.write(row["Descripción"])
            c1.write(row["Presentación"])
            c2.write(fmt_ars(row["Costo"]))
            c3.write(fmt_ars(row["Precio Venta"]))
            margen_pct = row["Margen"] / row["Precio Venta"] * 100
            c4.write(f"{fmt_ars(row['Margen'])}  ({margen_pct:.0f}%)")
            cantidad = c5.number_input(
                label="Cantidad",
                min_value=0,
                value=0,
                step=1,
                key=key,
                label_visibility="collapsed",
            )
            cantidades[key] = {"cantidad": cantidad, "row": row}

st.divider()

# ── Cálculo de resultados ────────────────────────────────────────────────────
resultados = []
for key, data in cantidades.items():
    q = data["cantidad"]
    row = data["row"]
    if q > 0:
        resultados.append({
            "Categoría":    row["Categoría"],
            "Descripción":  row["Descripción"],
            "Presentación": row["Presentación"],
            "Cantidad":     q,
            "Costo Total":  row["Costo"] * q,
            "Venta Total":  row["Precio Venta"] * q,
            "Ganancia":     row["Margen"] * q,
        })

total_costo  = sum(r["Costo Total"] for r in resultados)
total_venta  = sum(r["Venta Total"] for r in resultados)
total_margen = sum(r["Ganancia"]    for r in resultados)

# ── Métricas resumen ─────────────────────────────────────────────────────────
st.subheader("📊 Resumen de la simulación")

m1, m2, m3, m4 = st.columns(4)

m1.metric(
    "💰 Venta Total",
    fmt_ars(total_venta),
    delta=fmt_usd(total_venta / tipo_cambio) if tipo_cambio > 0 else None,
    delta_color="off",
)
m2.metric(
    "📦 Costo Total",
    fmt_ars(total_costo),
    delta=fmt_usd(total_costo / tipo_cambio) if tipo_cambio > 0 else None,
    delta_color="off",
)
m3.metric(
    "✅ Ganancia Neta",
    fmt_ars(total_margen),
    delta=fmt_usd(total_margen / tipo_cambio) if tipo_cambio > 0 else None,
)
margen_pct_total = (total_margen / total_venta * 100) if total_venta > 0 else 0
m4.metric(
    "📈 Margen %",
    f"{margen_pct_total:.1f} %",
)

# ── Detalle por producto ─────────────────────────────────────────────────────
if resultados:
    st.divider()
    st.subheader("🔍 Detalle por producto")

    df_res = pd.DataFrame(resultados)

    df_display = df_res.copy()
    for col in ["Costo Total", "Venta Total", "Ganancia"]:
        df_display[col] = df_res[col].apply(fmt_ars)

    st.dataframe(df_display, use_container_width=True, hide_index=True)

    # ── Gráfico de ganancia por producto ─────────────────────────────────────
    st.divider()
    st.subheader("📉 Ganancia por producto")

    df_chart = df_res.copy()
    df_chart["Producto"] = df_chart["Descripción"] + " — " + df_chart["Presentación"]
    df_chart = df_chart.set_index("Producto")[["Ganancia"]]
    st.bar_chart(df_chart, y_label="Ganancia (ARS)", use_container_width=True)

else:
    st.info("👆 Ingresá las cantidades estimadas arriba para ver los resultados de la simulación.")

# ── Footer ───────────────────────────────────────────────────────────────────
st.divider()
st.caption("Gira M19 · Simulador de ganancias · Datos: Ventas junio 2026")
