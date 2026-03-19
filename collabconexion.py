import streamlit as st
import pandas as pd
import re

# ==========================================
# 1. CONFIGURACIÓN DE LA PÁGINA
# ==========================================
st.set_page_config(
    page_title="Generador de Código Comercial",
    page_icon="⚙️",
    layout="wide"
)

# ==========================================
# 2. FUNCIONES DE LIMPIEZA Y TRANSFORMACIÓN
# ==========================================
def clean_value(val):
    """
    Limpia el valor extraído del Excel.
    Maneja notación científica, flotantes terminados en .0 y espacios.
    """
    if pd.isna(val) or val == "" or str(val).strip().lower() == "nan":
        return ""
    
    val_str = str(val).strip()
    
    # Manejar números leídos como flotantes o notación científica (ej. 1.93995e+12 o 20608153790.0)
    if re.match(r'^-?\d+(?:\.\d+)?(?:[eE][+\-]?\d+)?$', val_str):
        try:
            val_float = float(val_str)
            if val_float.is_integer():
                return str(int(val_float))
            return str(val_float)
        except ValueError:
            pass
            
    return val_str

def extract_data_to_dict(df):
    """Convierte el DataFrame a un diccionario anidado dict[SECCION][CAMPO] = VALOR"""
    data = {}
    for _, row in df.iterrows():
        seccion = str(row.get('SECCION', '')).strip().upper()
        campo = str(row.get('CAMPO', '')).strip()
        valor = clean_value(row.get('VALOR', ''))
        
        # Ignorar filas donde no hay sección ni campo (filas vacías arrastradas)
        if not seccion or not campo:
            continue
            
        if seccion not in data:
            data[seccion] = {}
        data[seccion][campo] = valor
    return data

# ==========================================
# 3. FUNCIONES DE VALIDACIÓN
# ==========================================
def validate_dataframe(df):
    """Valida reglas de negocio: obligatorios, formato RUC, formato email."""
    errors = []
    
    required_cols = ['SECCION', 'CAMPO', 'VALOR', 'OBLIGATORIO']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        errors.append(f"Faltan columnas requeridas: {', '.join(missing_cols)}")
        return errors 

    for index, row in df.iterrows():
        seccion = str(row.get('SECCION', '')).strip()
        campo = str(row.get('CAMPO', '')).strip()
        
        if not seccion and not campo:
            continue # Saltar filas totalmente vacías
            
        obligatorio = str(row.get('OBLIGATORIO', '')).strip().upper()
        valor = clean_value(row.get('VALOR', ''))
        
        # Validar obligatorios
        if obligatorio == 'SI' and not valor:
            errors.append(f"Fila {index + 2}: El campo '{campo}' en '{seccion}' es OBLIGATORIO.")
            continue 
            
        # Validar RUC (Numero de documento)
        if campo == 'Numero de documento' and valor:
            if not valor.isdigit() or len(valor) != 11:
                errors.append(f"Fila {index + 2}: El RUC '{valor}' es inválido. Debe tener 11 dígitos numéricos.")
                
        # Validar Correo
        if campo == 'Correo' and valor:
            if not re.match(r"[^@]+@[^@]+\.[^@]+", valor):
                errors.append(f"Fila {index + 2}: El correo '{valor}' tiene un formato inválido.")
                
    return errors

# ==========================================
# 4. GENERACIÓN DE CÓDIGO (TEMPLATE SEGURO)
# ==========================================
def generate_py_script(data):
    """Genera el código .py inyectando los valores de forma segura mediante replace()"""
    
    # Función auxiliar para no romper si el campo no existe
    def get_val(seccion, campo, default=""):
        return data.get(seccion.upper(), {}).get(campo, default)

    # DATOS_EMPRESA
    legal_name = get_val('DATOS_EMPRESA', 'Razon social')
    company_name = get_val('DATOS_EMPRESA', 'Nombre comercial')
    company_web = get_val('DATOS_EMPRESA', 'Pagina web')
    document_type = get_val('DATOS_EMPRESA', 'Tipo de documento', 'RUC')
    document_id = get_val('DATOS_EMPRESA', 'Numero de documento')
    phone = get_val('DATOS_EMPRESA', 'Telefono')
    if phone and not phone.startswith('+'): 
        phone = "+" + phone # Asegurar el + para el teléfono

    # DIRECCION
    addr_street = get_val('DIRECCION', 'Direccion')
    addr_zip = get_val('DIRECCION', 'Codigo postal')
    addr_city = get_val('DIRECCION', 'Ciudad')
    addr_state = get_val('DIRECCION', 'Departamento')
    addr_country = get_val('DIRECCION', 'Pais', 'PE')

    # CONTACTO
    first_name = get_val('CONTACTO', 'Nombre')
    last_name = get_val('CONTACTO', 'Apellido')
    email = get_val('CONTACTO', 'Correo')

    # CONFIGURACION
    service_type = get_val('CONFIGURACION', 'Tipo de servicio', 'PAYMENT_COLLECTOR')
    prefix = get_val('CONFIGURACION', 'Prefijo')
    prefix_code = f'"{prefix}"' if prefix else "None"

    # CUENTAS
    collect_currency = get_val('CUENTAS_RECAUDACION', 'Moneda', 'PEN')
    collect_account = get_val('CUENTAS_RECAUDACION', 'Numero de cuenta', 'xxx')
    
    bank_psp = get_val('CUENTAS_BANCARIAS', 'Banco', 'BCP')
    bank_currency = get_val('CUENTAS_BANCARIAS', 'Moneda', 'PEN')
    bank_account = get_val('CUENTAS_BANCARIAS', 'Numero de cuenta', 'xxx')
    bank_service_id = get_val('CUENTAS_BANCARIAS', 'Codigo de servicio', 'x')

    # NOTIFICACIONES
    webhook = get_val('NOTIFICACIONES', 'Webhook')

    # CONTRATO
    start_date = get_val('CONTRATO', 'Fecha inicio')
    end_date = get_val('CONTRATO', 'Fecha fin')

    # PLANTILLA BASE CON PLACEHOLDERS
    template = """############## COMPANY
LEGAL_NAME = "[LEGAL_NAME]"
COMPANY_NAME = "[COMPANY_NAME]"
COMPANY_WEB = "[COMPANY_WEB]"
DOCUMENT_TYPE = "[DOCUMENT_TYPE]"
DOCUMENT_ID = "[DOCUMENT_ID]"
PHONE = "[PHONE]"
#ADDRESS = {"street": "", "county": "", "zip": "", "city": "", "state": ""}
ADDRESS = {"street": "[ADDR_STREET]", "country": "[ADDR_COUNTRY]", "zip": "[ADDR_ZIP]", "city": "[ADDR_CITY]", "state": "[ADDR_STATE]"}
COUNTRY='PER'
#CODIGO_COMERCIO='' # KPSP-CNF
#CODIGO_COMERCIO=DOCUMENT_ID # KPSP-CNF
codigo_comercio=DOCUMENT_ID


user_first_name = "[FIRST_NAME]"
user_last_name = "[LAST_NAME]"
USER_NAME = f"{user_first_name} {user_last_name}".strip()
USER_EMAIL = "[EMAIL]"

PREFIX = [PREFIX]
SUB_TYPE = "[SERVICE_TYPE]"

LISTA_COLLECT=[
  {'CURRENCY':'[COLLECT_CURRENCY]','ACCOUNT_NUMBER':'[COLLECT_ACCOUNT]','SERVICE_FEE':{"fees": [{"fee": {"dr": 0, "cur": "[COLLECT_CURRENCY]", "max": 0.00, "min": 0.00, "tax": 18, "fixed": 0.00, "formula": "fixed + amount * dr / 100"}, "service": "payment"}]} },
]

  LISTA_BALANCE=[
    {'PSP':"[BANK_PSP]",'CURRENCY':'[BANK_CURRENCY]','ACCOUNT_NUMBER':'[BANK_ACCOUNT]','SERVICE_ID':'[BANK_SERVICE_ID]'},
    ]

LISTA_6_PSP=True #soporta alfanumerico y consulta codifo de pago con un digito a mas

## MODIFICABLE EN EL SISTEMA
NOTIFICATION_INVOICE_PAID = True
NOTIFICATION_WEBHOOK = "[WEBHOOK]"
NOTIFICATION_WEBHOOK_CONEXION_UNICA= True #### observado, debe ser cnx_unica_standard
CANT_LISTA_DEUDAS= True # False, <5

CHRONOLOGICAL_PAYMENT = True # DESHABLITADO

LATE_FEE_FORMULA_PEN = None
LATE_FEE_FORMULA_USD = None

_CONTRATO_start_date='[START_DATE]'
_CONTRATO_end_date='[END_DATE]'
"""

    # REEMPLAZOS
    replacements = {
        "[LEGAL_NAME]": legal_name,
        "[COMPANY_NAME]": company_name,
        "[COMPANY_WEB]": company_web,
        "[DOCUMENT_TYPE]": document_type,
        "[DOCUMENT_ID]": document_id,
        "[PHONE]": phone,
        "[ADDR_STREET]": addr_street,
        "[ADDR_COUNTRY]": addr_country,
        "[ADDR_ZIP]": addr_zip,
        "[ADDR_CITY]": addr_city,
        "[ADDR_STATE]": addr_state,
        "[FIRST_NAME]": first_name,
        "[LAST_NAME]": last_name,
        "[EMAIL]": email,
        "[PREFIX]": prefix_code,
        "[SERVICE_TYPE]": service_type,
        "[COLLECT_CURRENCY]": collect_currency,
        "[COLLECT_ACCOUNT]": collect_account,
        "[BANK_PSP]": bank_psp,
        "[BANK_CURRENCY]": bank_currency,
        "[BANK_ACCOUNT]": bank_account,
        "[BANK_SERVICE_ID]": bank_service_id,
        "[WEBHOOK]": webhook,
        "[START_DATE]": start_date,
        "[END_DATE]": end_date,
    }

    for key, val in replacements.items():
        template = template.replace(key, str(val))

    return template

# ==========================================
# 5. UI Y LÓGICA PRINCIPAL
# ==========================================
def main():
    st.title("🚀 Generador de Comercios - Python")
    st.markdown("Sube el archivo de configuración para generar automáticamente el código.")

    uploaded_file = st.file_uploader("Sube el Excel o CSV de configuración", type=["xlsx", "csv"])

    if uploaded_file is not None:
        try:
            # Leer dependiendo del tipo de archivo
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            
            # Limpieza básica para pandas
            df = df.dropna(how='all')
            df = df.fillna('')
            
            with st.expander("🔍 Vista previa de los datos", expanded=False):
                st.dataframe(df)

            errors = validate_dataframe(df)
            
            if errors:
                st.error("⚠️ Se encontraron errores en los datos. Por favor corrige el archivo:")
                for error in errors:
                    st.warning(f"- {error}")
            else:
                st.success("✅ ¡Datos validados correctamente!")
                
                data_dict = extract_data_to_dict(df)
                python_code = generate_py_script(data_dict)
                
                st.subheader("📝 Código Generado")
                st.code(python_code, language="python")
                
                b_code = python_code.encode('utf-8')
                ruc = data_dict.get('DATOS_EMPRESA', {}).get('Numero de documento', 'comercio')
                filename = f"{ruc}_config.py"
                
                st.download_button(
                    label="⬇️ Descargar archivo .py",
                    data=b_code,
                    file_name=filename,
                    mime="text/x-python"
                )

        except Exception as e:
            st.error(f"❌ Ocurrió un error inesperado al procesar el archivo: {e}")
            st.info("Asegúrate de que las columnas se llamen exactamente: SECCION, CAMPO, VALOR, OBLIGATORIO, DESCRIPCION.")

if __name__ == "__main__":
    main()
