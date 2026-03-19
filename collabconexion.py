import streamlit as st
import datetime
import re

# ==========================================
# CONFIGURACIÓN Y ESTILOS
# ==========================================
st.set_page_config(page_title="Onboarding Form - Generador", page_icon="📝")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #FF4B4B; color: white; }
    </style>
    """, unsafe_allow_html=True)

st.title("🚀 Formulario de Onboarding Comercial")
st.info("Completa los datos a continuación para generar el archivo de configuración técnica y el resumen para el cliente.")

# ==========================================
# FORMULARIO DE ENTRADA
# ==========================================
with st.form("onboarding_form"):
    # --- SECCIÓN 1: EMPRESA ---
    st.subheader("🏢 Datos de la Empresa")
    col1, col2 = st.columns(2)
    with col1:
        legal_name = st.text_input("Razón Social", placeholder="CREDIMINUTO PERU S.A.C.")
        company_name = st.text_input("Nombre Comercial", placeholder="CREDISMART")
        document_id = st.text_input("RUC (11 dígitos)", max_chars=11)
    with col2:
        company_web = st.text_input("Página Web (Opcional)", placeholder="https://...")
        phone = st.text_input("Teléfono de Contacto", placeholder="+51939358348")
        country_code = st.selectbox("País", ["PER", "MEX", "COL"], index=0)

    # --- SECCIÓN 2: DIRECCIÓN ---
    st.subheader("📍 Dirección Fiscal")
    street = st.text_input("Dirección (Calle/Av/Mz)", placeholder="Av. Ejemplo 123")
    col_dir1, col_dir2, col_dir3 = st.columns(3)
    with col_dir1:
        city = st.text_input("Ciudad", value="Lima")
    with col_dir2:
        state = st.text_input("Departamento/Estado", value="Lima")
    with col_dir3:
        zip_code = st.text_input("Código Postal", value="15001")

    # --- SECCIÓN 3: CONTACTO ---
    st.subheader("👤 Contacto de Onboarding")
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        u_first_name = st.text_input("Nombres", placeholder="Edith")
        u_email = st.text_input("Correo Electrónico", placeholder="usuario@empresa.com")
    with col_c2:
        u_last_name = st.text_input("Apellidos", placeholder="Díaz")

    # --- SECCIÓN 4: CUENTAS Y BANCOS ---
    st.subheader("💰 Configuración Bancaria")
    col_b1, col_b2 = st.columns(2)
    with col_b1:
        st.markdown("**Cuenta de Recaudación (Collect)**")
        curr_collect = st.selectbox("Moneda Recaudación", ["PEN", "USD"])
        acc_collect = st.text_input("Número de Cuenta Recaudación", placeholder="xxx")
    with col_b2:
        st.markdown("**Cuenta de Abono (Balance)**")
        psp = st.text_input("Banco (PSP)", value="BCP")
        acc_bank = st.text_input("Número de Cuenta Bancaria", placeholder="1939945440088")
        service_id = st.text_input("Service ID (Código de Servicio)", placeholder="1055")

    # --- SECCIÓN 5: CONFIGURACIÓN Y CONTRATO ---
    st.subheader("📅 Detalles del Servicio")
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        webhook = st.text_input("URL Webhook", value="https://cmin.io/api/kashio-interconnect-payment-notification")
        prefix = st.text_input("Prefijo de Pago (Opcional)", value="")
    with col_s2:
        start_date = st.date_input("Inicio de Contrato", datetime.date.today())
        end_date = st.date_input("Fin de Contrato", datetime.date.today() + datetime.timedelta(days=365))

    submitted = st.form_submit_button("GENERAR ARCHIVOS")

# ==========================================
# LÓGICA DE GENERACIÓN
# ==========================================
if submitted:
    # 1. Validaciones
    errors = []
    if not document_id.isdigit() or len(document_id) != 11:
        errors.append("El RUC debe ser numérico y tener 11 dígitos.")
    if not re.match(r"[^@]+@[^@]+\.[^@]+", u_email):
        errors.append("El formato del correo electrónico no es válido.")
    if not legal_name or not company_name:
        errors.append("La Razón Social y el Nombre Comercial son obligatorios.")

    if errors:
        for err in errors:
            st.error(err)
    else:
        # --- GENERACIÓN DE CÓDIGO .PY (Exactamente como se pidió) ---
        prefix_val = f'"{prefix}"' if prefix else "None"
        
        # Usamos f-strings escapando las llaves con {{ }}
        py_code = f"""############## COMPANY
LEGAL_NAME = "{legal_name.upper()}"
COMPANY_NAME = "{company_name.upper()}"
COMPANY_WEB = "{company_web}"
DOCUMENT_TYPE = "RUC"
DOCUMENT_ID = "{document_id}"
PHONE = "{phone}"
#ADDRESS = {{"street": "", "county": "", "zip": "", "city": "", "state": ""}}
ADDRESS = {{"street": "{street}", "country": "PE", "zip": "{zip_code}", "city": "{city}", "state": "{state}", "country": "PE"}}
#ADDRESS = {{"street": "", "country": "MX", "zip": "", "city": "", "state": "", "country": "PE"}}
COUNTRY='{country_code}'
#CODIGO_COMERCIO='' # KPSP-CNF
#CODIGO_COMERCIO=DOCUMENT_ID # KPSP-CNF
codigo_comercio=DOCUMENT_ID


user_first_name = "{u_first_name}"
user_last_name = "{u_last_name}"
USER_NAME = f"{{user_first_name}} {{user_last_name}}".strip()
USER_EMAIL = "{u_email}"

PREFIX = {prefix_val}
SUB_TYPE = "PAYMENT_COLLECTOR"

LISTA_COLLECT=[
  {{'CURRENCY':'{curr_collect}','ACCOUNT_NUMBER':'{acc_collect}','SERVICE_FEE':{{"fees": [{{"fee": {{"dr": 0, "cur": "{curr_collect}", "max": 0.00, "min": 0.00, "tax": 18, "fixed": 0.00, "formula": "fixed + amount * dr / 100"}}, "service": "payment"}}]}} }},
]

  LISTA_BALANCE=[
    {{'PSP':"{psp}",'CURRENCY':'{curr_collect}','ACCOUNT_NUMBER':'{acc_bank}','SERVICE_ID':'{service_id}'}},
    ]


LISTA_6_PSP=True #soporta alfanumerico y consulta codifo de pago con un digito a mas

## MODIFICABLE EN EL SISTEMA
NOTIFICATION_INVOICE_PAID = True
NOTIFICATION_WEBHOOK = "{webhook}"
NOTIFICATION_WEBHOOK_CONEXION_UNICA= True #### observado, debe ser cnx_unica_standard
CANT_LISTA_DEUDAS= True # False, <5

CHRONOLOGICAL_PAYMENT = True # DESHABLITADO

LATE_FEE_FORMULA_PEN = None
LATE_FEE_FORMULA_USD = None

_CONTRATO_start_date='{start_date.isoformat()}T23:40:41.012522Z'
_CONTRATO_end_date='{end_date.isoformat()}T23:40:41.012574Z'
"""

        # --- GENERACIÓN DE RESUMEN PARA USUARIO (TXT) ---
        user_summary = f"""RESUMEN DE CONFIGURACIÓN DE COMERCIO
==========================================
FECHA DE REGISTRO: {datetime.date.today()}

1. DATOS DE LA EMPRESA
----------------------
Razón Social: {legal_name}
Nombre Comercial: {company_name}
RUC: {document_id}
País: {country_code}

2. CONTACTO DESIGNADO
----------------------
Nombre: {u_first_name} {u_last_name}
Email: {u_email}

3. INFORMACIÓN BANCARIA
----------------------
Recaudación ({curr_collect}): Cuenta {acc_collect}
Banco de Abono: {psp}
Número de Cuenta: {acc_bank}
ID de Servicio: {service_id}

4. CONFIGURACIÓN TÉCNICA
----------------------
Webhook: {webhook}
Vigencia: {start_date} hasta {end_date}

==========================================
Archivo generado automáticamente para Onboarding.
"""

        st.success("✅ ¡Configuración generada con éxito!")

        # Visualización y Descargas
        st.subheader("📦 Descargar Archivos")
        col_dl1, col_dl2 = st.columns(2)
        
        with col_dl1:
            st.download_button(
                label="🐍 Descargar .py (Técnico)",
                data=py_code,
                file_name=f"config_{document_id}.py",
                mime="text/x-python"
            )
        
        with col_dl2:
            st.download_button(
                label="📄 Descargar Resumen (.txt)",
                data=user_summary,
                file_name=f"resumen_{company_name.replace(' ', '_')}.txt",
                mime="text/plain"
            )

        with st.expander("👁️ Ver código generado"):
            st.code(py_code, language="python")

        with st.expander("👁️ Ver resumen para usuario"):
            st.text(user_summary)
