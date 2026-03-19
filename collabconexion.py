import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Conexión Única Generator", layout="wide")

st.title("⚙️ Generador Conexión Única")

file = st.file_uploader("Sube tu Excel", type=["xlsx"])

# ---------------- HELPERS ---------------- #

def clean_text(val):
    if pd.isna(val):
        return ""
    return str(val).strip()

def fix_account_number(val):
    try:
        if pd.isna(val):
            return ""
        val = str(val)
        if "E+" in val:
            return str(int(float(val)))
        return val
    except:
        return str(val)

def validar_ruc(ruc):
    return str(ruc).isdigit() and len(str(ruc)) == 11

def validar_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", str(email))

# ---------------- MAIN ---------------- #

if file:
    df = pd.read_excel(file)

    # Limpiar filas vacías
    df = df.dropna(how="all")

    # Normalizar columnas
    df.columns = df.columns.str.strip()

    # Convertir a diccionario
    data = {}

    for _, row in df.iterrows():
        seccion = clean_text(row["SECCION"])
        campo = clean_text(row["CAMPO"])
        valor = clean_text(row["VALOR"])

        if not seccion or not campo:
            continue

        if seccion not in data:
            data[seccion] = {}

        data[seccion][campo] = valor

    # ---------------- VALIDACIONES ---------------- #

    errores = []

    try:
        ruc = data["DATOS_EMPRESA"]["Numero de documento"]
        email = data["CONTACTO"]["Correo"]

        if not validar_ruc(ruc):
            errores.append("RUC inválido")

        if not validar_email(email):
            errores.append("Email inválido")

    except:
        errores.append("Faltan datos clave (RUC o Email)")

    if errores:
        st.error("Errores encontrados:")
        for e in errores:
            st.write(f"- {e}")
        st.stop()

    # ---------------- DATOS ---------------- #

    emp = data["DATOS_EMPRESA"]
    dir = data.get("DIRECCION", {})
    con = data["CONTACTO"]
    cfg = data["CONFIGURACION"]
    rec = data["CUENTAS_RECAUDACION"]
    ban = data["CUENTAS_BANCARIAS"]
    noti = data["NOTIFICACIONES"]
    cont = data["CONTRATO"]

    cuenta_bancaria = fix_account_number(ban.get("Numero de cuenta"))

    # ---------------- CODIGO FINAL ---------------- #

    codigo = f'''############## COMPANY
LEGAL_NAME = "{emp.get("Razon social")}"
COMPANY_NAME = "{emp.get("Nombre comercial")}"
COMPANY_WEB = "{emp.get("Pagina web","")}"
DOCUMENT_TYPE = "{emp.get("Tipo de documento")}"
DOCUMENT_ID = "{emp.get("Numero de documento")}"
PHONE = "+{emp.get("Telefono")}"

#ADDRESS = {{"street": "", "county": "", "zip": "", "city": "", "state": ""}}
ADDRESS = {{"street": "{dir.get("Direccion","")}", "country": "{dir.get("Pais","PE")}", "zip": "{dir.get("Codigo postal","")}", "city": "{dir.get("Ciudad","")}", "state": "{dir.get("Departamento","")}", "country": "{dir.get("Pais","PE")}"}}
#ADDRESS = {{"street": "", "country": "MX", "zip": "", "city": "", "state": "", "country": "PE"}}
COUNTRY='{emp.get("Pais")}'
#CODIGO_COMERCIO='' # KPSP-CNF
#CODIGO_COMERCIO=DOCUMENT_ID # KPSP-CNF
codigo_comercio=DOCUMENT_ID


user_first_name = "{con.get("Nombre")}"
user_last_name = "{con.get("Apellido")}"
USER_NAME = f"{{user_first_name}} {{user_last_name}}".strip()
USER_EMAIL = "{con.get("Correo")}"

PREFIX = None
SUB_TYPE = "{cfg.get("Tipo de servicio")}"

LISTA_COLLECT=[
  {{'CURRENCY':'{rec.get("Moneda")}',
    'ACCOUNT_NUMBER':'{rec.get("Numero de cuenta")}',
    'SERVICE_FEE':{{"fees": [{{"fee": {{
        "dr": {rec.get("Comision (%)")},
        "cur": "{rec.get("Moneda")}",
        "max": 0.00,
        "min": 0.00,
        "tax": {rec.get("Impuesto (%)")},
        "fixed": {rec.get("Comision fija")},
        "formula": "fixed + amount * dr / 100"
    }}, "service": "payment"}}]}}
  }},
]

  LISTA_BALANCE=[
    {{'PSP':"{ban.get("Banco")}",
      'CURRENCY':'{ban.get("Moneda")}',
      'ACCOUNT_NUMBER':'{cuenta_bancaria}',
      'SERVICE_ID':'{ban.get("Codigo de servicio")}'}
    }}
    ]

LISTA_6_PSP={str(cfg.get("Soporta codigos largos")).upper()=="SI"}

## MODIFICABLE EN EL SISTEMA
NOTIFICATION_INVOICE_PAID = True
NOTIFICATION_WEBHOOK = "{noti.get("Webhook")}"
NOTIFICATION_WEBHOOK_CONEXION_UNICA= True #### observado, debe ser cnx_unica_standard
CANT_LISTA_DEUDAS= True # False, <5

CHRONOLOGICAL_PAYMENT = {str(cfg.get("Pagos en orden cronologico")).upper()=="SI"} # DESHABLITADO

LATE_FEE_FORMULA_PEN = None
LATE_FEE_FORMULA_USD = None

_CONTRATO_start_date='{cont.get("Fecha inicio")}'
_CONTRATO_end_date='{cont.get("Fecha fin")}'
'''

    # ---------------- OUTPUT ---------------- #

    st.success("Código generado correctamente")

    st.code(codigo, language="python")

    st.download_button(
        "Descargar .py",
        codigo,
        "conexion_unica.py"
    )
