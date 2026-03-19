import streamlit as st
import pandas as pd
import re
from io import StringIO

st.set_page_config(page_title="Conexión Única Generator", layout="wide")

st.title("⚙️ Generador Conexión Única")
st.write("Sube el Excel completado por onboarding")

file = st.file_uploader("Subir archivo Excel", type=["xlsx"])

# ---------------- VALIDACIONES ---------------- #

def validar_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", str(email))

def validar_ruc(ruc):
    return str(ruc).isdigit() and len(str(ruc)) == 11

# ---------------- PROCESAMIENTO ---------------- #

if file:
    df = pd.read_excel(file)

    # Normalizar columnas
    df.columns = df.columns.str.strip().str.upper()

    # Validar columnas esperadas
    required_cols = ["SECCION", "CAMPO", "VALOR", "OBLIGATORIO"]
    if not all(col in df.columns for col in required_cols):
        st.error("El archivo no tiene el formato correcto.")
        st.stop()

    # Validar obligatorios
    errores = []
    for _, row in df.iterrows():
        if str(row["OBLIGATORIO"]).upper() == "SI" and pd.isna(row["VALOR"]):
            errores.append(f"Falta valor en: {row['SECCION']} - {row['CAMPO']}")

    # Convertir a diccionario
    data = {}
    for _, row in df.iterrows():
        seccion = row["SECCION"]
        campo = row["CAMPO"]
        valor = row["VALOR"]

        if seccion not in data:
            data[seccion] = {}

        # Permitir múltiples valores (listas)
        if campo in data[seccion]:
            if not isinstance(data[seccion][campo], list):
                data[seccion][campo] = [data[seccion][campo]]
            data[seccion][campo].append(valor)
        else:
            data[seccion][campo] = valor

    # Validaciones específicas
    try:
        ruc = data["DATOS_EMPRESA"]["Numero de documento"]
        email = data["CONTACTO"]["Correo"]

        if not validar_ruc(ruc):
            errores.append("RUC inválido")

        if not validar_email(email):
            errores.append("Email inválido")
    except:
        errores.append("Error leyendo RUC o Email")

    if errores:
        st.error("Errores encontrados:")
        for e in errores:
            st.write(f"- {e}")
        st.stop()

    # ---------------- GENERACIÓN DE CÓDIGO ---------------- #

    empresa = data["DATOS_EMPRESA"]
    direccion = data["DIRECCION"]
    contacto = data["CONTACTO"]
    config = data["CONFIGURACION"]
    notif = data["NOTIFICACIONES"]
    contrato = data["CONTRATO"]

    # LISTA COLLECT
    collect = f"""
LISTA_COLLECT=[
  {{
    'CURRENCY':'{data["CUENTAS_RECAUDACION"]["Moneda"]}',
    'ACCOUNT_NUMBER':'{data["CUENTAS_RECAUDACION"]["Numero de cuenta"]}',
    'SERVICE_FEE':{{"fees": [{{"fee": {{
        "dr": {data["CUENTAS_RECAUDACION"]["Comision (%)"]},
        "cur": "{data["CUENTAS_RECAUDACION"]["Moneda"]}",
        "max": 0.00,
        "min": 0.00,
        "tax": {data["CUENTAS_RECAUDACION"]["Impuesto (%)"]},
        "fixed": {data["CUENTAS_RECAUDACION"]["Comision fija"]},
        "formula": "fixed + amount * dr / 100"
    }}, "service": "payment"}}]}}
  }}
]
"""

    # LISTA BALANCE
    balance = f"""
LISTA_BALANCE=[
  {{
    'PSP':"{data["CUENTAS_BANCARIAS"]["Banco"]}",
    'CURRENCY':'{data["CUENTAS_BANCARIAS"]["Moneda"]}',
    'ACCOUNT_NUMBER':'{data["CUENTAS_BANCARIAS"]["Numero de cuenta"]}',
    'SERVICE_ID':'{data["CUENTAS_BANCARIAS"]["Codigo de servicio"]}'
  }}
]
"""

    codigo = f"""
############## COMPANY
LEGAL_NAME = "{empresa['Razon social']}"
COMPANY_NAME = "{empresa['Nombre comercial']}"
COMPANY_WEB = "{empresa.get('Pagina web','')}"
DOCUMENT_TYPE = "{empresa['Tipo de documento']}"
DOCUMENT_ID = "{empresa['Numero de documento']}"
PHONE = "{empresa['Telefono']}"

ADDRESS = {{
    "street": "{direccion.get('Direccion','')}",
    "country": "{direccion.get('Pais','PE')}",
    "zip": "{direccion.get('Codigo postal','')}",
    "city": "{direccion.get('Ciudad','')}",
    "state": "{direccion.get('Departamento','')}"
}}

COUNTRY='{empresa['Pais']}'
codigo_comercio=DOCUMENT_ID

user_first_name = "{contacto['Nombre']}"
user_last_name = "{contacto['Apellido']}"
USER_NAME = f"{{user_first_name}} {{user_last_name}}".strip()
USER_EMAIL = "{contacto['Correo']}"

PREFIX = None
SUB_TYPE = "{config['Tipo de servicio']}"

{collect}

{balance}

LISTA_6_PSP={str(config['Soporta codigos largos']).upper() == 'SI'}

NOTIFICATION_INVOICE_PAID = True
NOTIFICATION_WEBHOOK = "{notif['Webhook']}"
NOTIFICATION_WEBHOOK_CONEXION_UNICA= True

CHRONOLOGICAL_PAYMENT = {str(config['Pagos en orden cronologico']).upper() == 'SI'}

_CONTRATO_start_date='{contrato['Fecha inicio']}'
_CONTRATO_end_date='{contrato['Fecha fin']}'
"""

    # ---------------- OUTPUT ---------------- #

    st.success("Código generado correctamente")

    st.code(codigo, language="python")

    st.download_button(
        label="Descargar .py",
        data=codigo,
        file_name="conexion_unica.py",
        mime="text/plain"
    )
