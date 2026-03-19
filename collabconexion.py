import streamlit as st
import pandas as pd
import re
from io import BytesIO

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
    if pd.isna(val) or val == "":
        return ""
    
    val_str = str(val).strip()
    
    # Si pandas lo leyó como notación científica o float (ej. 1.93995e+12 o 1939950000000.0)
    if re.match(r'^-?\d+(?:\.\d+)?(?:[eE][+\-]?\d+)?$', val_str):
        try:
            # Convertimos a float y luego a entero para quitar decimales, luego a string
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
    
    # Validar que existan las columnas mínimas
    required_cols = ['SECCION', 'CAMPO', 'VALOR', 'OBLIGATORIO']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        errors.append(f"Faltan columnas requeridas en el Excel: {', '.join(missing_cols)}")
        return errors # Si faltan columnas, no podemos seguir validando

    for index, row in df.iterrows():
        seccion = str(row.get('SECCION', '')).strip()
        campo = str(row.get('CAMPO', '')).strip()
        obligatorio = str(row.get('OBLIGATORIO', '')).strip().upper()
        valor_raw = row.get('VALOR', '')
        valor = clean_value(valor_raw)
        
        # Validar obligatorios
        if obligatorio == 'SI' and not valor:
            errors.append(f"Fila {index + 2}: El campo '{campo}' de la sección '{seccion}' es OBLIGATORIO.")
            continue # Si está vacío, no evaluamos el resto de reglas para esta fila
            
        # Validar RUC (asumiendo que la palabra 'ruc' o 'document' está en el nombre del campo)
        if 'ruc' in campo.lower() and valor:
            if not valor.isdigit() or len(valor) != 11:
                errors.append(f"Fila {index + 2}: El RUC '{valor}' es inválido. Debe tener 11 dígitos numéricos exactos.")
                
        # Validar Correo
        if ('correo' in campo.lower() or 'email' in campo.lower()) and valor:
            if not re.match(r"[^@]+@[^@]+\.[^@]+", valor):
                errors.append(f"Fila {index + 2}: El formato del correo '{valor}' es inválido.")
                
    return errors

# ==========================================
# 4. GENERACIÓN DE CÓDIGO (TEMPLATE SEGURO)
# ==========================================
def generate_py_script(data_dict):
    """
    Genera el código .py inyectando los valores de forma segura mediante replace()
    para evitar conflictos de f-strings con los diccionarios JSON internos.
    """
    
    # Funciones auxiliares para obtener valores con default ""
    def get_val(seccion, campo, default=""):
        return data_dict.get(seccion.upper(), {}).get(campo, default)

    # 1. Extracción de variables (Ajusta los nombres exactos del "CAMPO" según tu Excel)
    legal_name = get_val('DATOS_EMPRESA', 'Razon social')
    company_name = get_val('DATOS_EMPRESA', 'Nombre comercial')
    document_id = get_val('DATOS_EMPRESA', 'RUC') # Ajusta si el campo se llama distinto
    phone = get_val('CONTACTO', 'Telefono')
    email = get_val('CONTACTO', 'Correo')
    
    # Separación de Nombres y Apellidos (si vienen en un solo campo, o usa los campos separados)
    nombres = get_val('CONTACTO', 'Nombres', 'Usuario') 
    apellidos = get_val('CONTACTO', 'Apellidos', '')
    account_number = get_val('CUENTAS_BANCARIAS', 'Numero de cuenta')

    # 2. Plantilla Base cruda (Uso de marcadores [PLACEHOLDERS] para reemplazar)
    template = """############## COMPANY
LEGAL_NAME = "[LEGAL_NAME]"
COMPANY_NAME = "[COMPANY_NAME]"
COMPANY_WEB = ""
DOCUMENT_TYPE = "RUC"
DOCUMENT_ID = "[DOCUMENT_ID]"
PHONE = "[PHONE]"
#ADDRESS = {"street": "", "county": "", "zip": "", "city": "", "state": ""}
ADDRESS = {"street": "", "country": "PE", "zip": "", "city": "", "state": "", "country": "PE"}
#ADDRESS = {"street": "", "country": "MX", "zip": "", "city": "", "state": "", "country": "PE"}
COUNTRY='PER'
#CODIGO_COMERCIO='' # KPSP-CNF
#CODIGO_COMERCIO=DOCUMENT_ID # KPSP-CNF
codigo_comercio=DOCUMENT_ID


user_first_name = "[USER_FIRST_NAME]"
user_last_name = "[USER_LAST_NAME]"
USER_NAME = f"{user_first_name} {user_last_name}".strip()
USER_EMAIL = "[USER_EMAIL]"

PREFIX = None
SUB_TYPE = "PAYMENT_COLLECTOR"

LISTA_COLLECT=[
  {'CURRENCY':'PEN','ACCOUNT_NUMBER':'[ACCOUNT_NUMBER]','SERVICE_FEE':{"fees": [{"fee": {"dr": 0, "cur": "PEN", "max": 0.00, "min": 0.00, "tax": 18, "fixed": 0.00, "formula": "fixed + amount * dr / 100"}, "service": "payment"}]} },
  #{'CURRENCY':'USD','ACCOUNT_NUMBER':'xxx','SERVICE_FEE':{"fees": [{"fee": {"dr": 0, "cur": "USD", "max": 0.00, "min": 0.00, "tax": 18, "fixed": 0.00, "formula": "fixed + amount * dr / 100"}, "service": "payment"}]} }
]

  LISTA_BALANCE=[
    {'PSP':"BCP",'CURRENCY':'PEN','ACCOUNT_NUMBER':'[ACCOUNT_NUMBER]','SERVICE_ID':'1055'},
    #{'PSP':"BBVA",'CURRENCY':'PEN','ACCOUNT_NUMBER':'001109670100005237','SERVICE_ID':'0022410'},
    #{'PSP':"Scotiabank",'CURRENCY':'PEN','ACCOUNT_NUMBER':'xxx','SERVICE_ID':'x'},
    #{'PSP':"Interbank",'CURRENCY':'PEN','ACCOUNT_NUMBER':'xxx','SERVICE_ID':'x'},
    #{'PSP':"Kasnet",'CURRENCY':'PEN','ACCOUNT_NUMBER':'xxx','SERVICE_ID':'x'},
    #{'PSP':"Cmac Huancayo",'CURRENCY':'PEN','ACCOUNT_NUMBER':'xxx','SERVICE_ID':'x'},
    #{'PSP':"BCP",'CURRENCY':'USD','ACCOUNT_NUMBER':'1939945440088','SERVICE_ID':'1055'},
    #{'PSP':"BBVA",'CURRENCY':'USD','ACCOUNT_NUMBER':'001109670100005237','SERVICE_ID':'0022410'},
    #{'PSP':"Scotiabank",'CURRENCY':'USD','ACCOUNT_NUMBER':'xxx','SERVICE_ID':'x'},
    #{'PSP':"Interbank",'CURRENCY':'USD','ACCOUNT_NUMBER':'xxx','SERVICE_ID':'x'},
    #{'PSP':"Kasnet",'CURRENCY':'USD','ACCOUNT_NUMBER':'xxx','SERVICE_ID':'x'},
    #{'PSP':"Cmac Huancayo",'CURRENCY':'USD','ACCOUNT_NUMBER':'xxx','SERVICE_ID':'x'}
    ]


LISTA_6_PSP=True #soporta alfanumerico y consulta codifo de pago con un digito a mas

## MODIFICABLE EN EL SISTEMA
NOTIFICATION_INVOICE_PAID = True
NOTIFICATION_WEBHOOK = "https://cmin.io/api/kashio-interconnect-payment-notification"
NOTIFICATION_WEBHOOK_CONEXION_UNICA= True #### observado, debe ser cnx_unica_standard
CANT_LISTA_DEUDAS= True # False, <5

CHRONOLOGICAL_PAYMENT = True # DESHABLITADO

LATE_FEE_FORMULA_PEN = None
LATE_FEE_FORMULA_USD = None

_CONTRATO_start_date='2025-11-19T23:40:41.012522Z'
_CONTRATO_end_date='2026-11-19T23:40:41.012574Z'
"""

    # 3. Reemplazo seguro de valores
    final_code = template.replace("[LEGAL_NAME]", legal_name)
    final_code = final_code.replace("[COMPANY_NAME]", company_name)
    final_code = final_code.replace("[DOCUMENT_ID]", document_id)
    final_code = final_code.replace("[PHONE]", phone)
    final_code = final_code.replace("[USER_FIRST_NAME]", nombres)
    final_code = final_code.replace("[USER_LAST_NAME]", apellidos)
    final_code = final_code.replace("[USER_EMAIL]", email)
    final_code = final_code.replace("[ACCOUNT_NUMBER]", account_number)

    return final_code

# ==========================================
# 5. UI Y LÓGICA PRINCIPAL (STREAMLIT)
# ==========================================
def main():
    st.title("🚀 Generador de Comercios - Python")
    st.markdown("Sube el archivo Excel proporcionado por el equipo de Onboarding para generar automáticamente el código de integración.")

    uploaded_file = st.file_uploader("Sube el Excel de configuración (.xlsx)", type=["xlsx"])

    if uploaded_file is not None:
        try:
            # 1. Leer Excel y eliminar filas completamente vacías
            df = pd.read_excel(uploaded_file)
            df = df.dropna(how='all')
            df = df.fillna('')
            
            with st.expander("🔍 Vista previa de los datos leídos", expanded=False):
                st.dataframe(df)

            # 2. Validar Datos
            errors = validate_dataframe(df)
            
            if errors:
                st.error("⚠️ Se encontraron errores en los datos del Excel. Por favor corrige el archivo y vuelve a subirlo:")
                for error in errors:
                    st.warning(f"- {error}")
            else:
                st.success("✅ ¡Datos validados correctamente! No hay errores críticos.")
                
                # 3. Procesar a diccionario
                data_dict = extract_data_to_dict(df)
                
                # 4. Generar Código
                python_code = generate_py_script(data_dict)
                
                st.subheader("📝 Código Generado")
                st.code(python_code, language="python")
                
                # 5. Botón de Descarga
                # Convertimos el string a bytes para la descarga
                b_code = python_code.encode('utf-8')
                filename = data_dict.get('DATOS_EMPRESA', {}).get('RUC', 'comercio') + "_config.py"
                
                st.download_button(
                    label="⬇️ Descargar archivo .py",
                    data=b_code,
                    file_name=filename,
                    mime="text/x-python"
                )

        except Exception as e:
            st.error(f"❌ Ocurrió un error inesperado al procesar el archivo: {e}")
            st.info("Revisa que el archivo subido sea un Excel válido y tenga el formato de columnas requerido.")

if __name__ == "__main__":
    main()
