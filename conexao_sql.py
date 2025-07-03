import streamlit as st
import msal
import requests
import pandas as pd
from datetime import datetime, timedelta

# === CREDENCIAIS DO STREAMLIT SECRETS ===
client_id = st.secrets["CLIENT_ID"]
client_secret = st.secrets["CLIENT_SECRET"]
tenant_id = st.secrets["TENANT_ID"]
site_name = st.secrets["SITE_NAME"]
site_domain = st.secrets["SITE_DOMAIN"]
list_name = st.secrets["LIST_NAME"]

# === AUTENTICAÇÃO COM MSAL ===
authority = f"https://login.microsoftonline.com/{tenant_id}"
scopes = ["https://graph.microsoft.com/.default"]

def obter_token():
    app = msal.ConfidentialClientApplication(
        client_id, authority=authority, client_credential=client_secret
    )
    token_response = app.acquire_token_for_client(scopes=scopes)
    if "access_token" in token_response:
        return token_response["access_token"]
    else:
        raise Exception(f"Erro ao obter token: {token_response}")

# === OBTÉM SITE ID DO SHAREPOINT ===
def obter_site_id(token):
    url = f"https://graph.microsoft.com/v1.0/sites/{site_domain}:/sites/{site_name}"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()["id"]

# === OBTÉM DADOS DA LISTA DO SHAREPOINT ===
def obter_dados_sharepoint():
    token = obter_token()
    site_id = obter_site_id(token)

    base_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/{list_name}/items"
    params = {"$expand": "fields", "$top": 5000}
    headers = {"Authorization": f"Bearer {token}"}

    registros = []
    url = base_url

    while url:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()

        for item in data["value"]:
            registro = item["fields"]
            registro["ID"] = int(item["id"])
            registro["Created"] = item.get("createdDateTime")
            registros.append(registro)

        url = data.get("@odata.nextLink", None)
        params = None  # Só usar no primeiro request

    df = pd.DataFrame(registros)

    # Conversões seguras de data
    if "Created" in df.columns:
        df["Created"] = pd.to_datetime(df["Created"], utc=True, errors="coerce")
        df = df.dropna(subset=["Created"])

    if "DATA_x0020_EXECU_x00c7__x00c3_O" in df.columns:
        df["DATA_EXECUCAO"] = pd.to_datetime(df["DATA_x0020_EXECU_x00c7__x00c3_O"], errors="coerce")

    # Filtra últimos 90 dias
    ultimos_90_dias = pd.Timestamp.utcnow() - pd.Timedelta(days=90)
    df = df[df["Created"] >= ultimos_90_dias]

    # Limita a 10.000 registros
    df = df.sort_values(by="ID", ascending=False).head(10000).reset_index(drop=True)

    return df

# === ATUALIZA UM CAMPO DE UM ITEM DO SHAREPOINT ===
def editar_item_sharepoint(item_id, campo, novo_valor):
    token = obter_token()
    site_id = obter_site_id(token)

    url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists/{list_name}/items/{item_id}/fields"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    data = {
        "fields": {
            campo: novo_valor
        }
    }

    response = requests.patch(url, headers=headers, json=data)

    if response.status_code == 200:
        print(f"Item {item_id} atualizado com sucesso.")
        return True
    else:
        print(f"Erro ao atualizar item {item_id}: {response.status_code} - {response.text}")
        return False
