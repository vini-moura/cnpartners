from PIL import Image
from fpdf import FPDF
import requests
from requests.auth import HTTPBasicAuth
import json
import pandas as pd

'''imagens = [
    "C:/Users/vinic/OneDriveDocumentos/murilo/proposta de financiamento 1.jpg",
]


pdf = FPDF()

for imagem in imagens:
    img = Image.open(imagem)
    if img.mode == 'RGBA':
        img = img.convert('RGB')
    width, height = img.size
    pdf.add_page()

    aspect_ratio = width / height
    pdf_width = pdf.w - 20
    pdf_height = pdf_width / aspect_ratio

    pdf.image(imagem, 10, 10, pdf_width, pdf_height)

# Salvar o PDF
pdf.output("proposta de financiamento.pdf")'''


def get_access_token():
    url = "https://api.anbima.com.br/oauth/access-token"
    header = {
        "Content-Type": "application/json",
    }
    data = {
        "grant_type": "client_credentials"
    }
    response = requests.post(url, headers=header, json=data, auth=HTTPBasicAuth("UC9UbnNaIKMz", "QAXbskiof5Gk"))
    if response.status_code == 200:
        json_str = response.json()
    status_code, json_str = get_access_token()
    dados = json.loads(json_str)
    token = dados['access_token']
    return token


def get_td():
    token = get_access_token()
    url = 'https://api-sandbox.anbima.com.br/feed/precos-indices/v1/titulos-publicos/mercado-secundario-TPF'
    header = {
        'Content-Type': 'application/json',
        "client_id": "UC9UbnNaIKMz",
        "access_token": token
    }
    response = requests.get(url, headers=header)
    try:
        json_data = response.json()
        if response.status_code == 200:
            data = response.json()
            df = pd.DataFrame(data)
            df.to_csv('titulos publicos.csv', index=False)
            return df

    except json.JSONDecodeError:
        return response.text

def get_debenture():
    url = 'https://api-sandbox.anbima.com.br/feed/precos-indices/v1/debentures/mercado-secundario'
    header = {
        'Content-Type': 'application/json',
        "client_id": "UC9UbnNaIKMz",
        "access_token": token
    }
    response = requests.get(url, headers=header)
    try:
        json_data = response.json()
        if response.status_code == 200:
            data = response.json()
            df = pd.DataFrame(data)
            df.to_csv('debenture.csv', index=False)
            return df

    except json.JSONDecodeError:
        return response.text

def get_debenture():
    url = 'https://api-sandbox.anbima.com.br/feed/precos-indices/v1/cri-cra/mercado-secundario'
    header = {
        'Content-Type': 'application/json',
        "client_id": "UC9UbnNaIKMz",
        "access_token": token
    }
    response = requests.get(url, headers=header)
    try:
        json_data = response.json()
        if response.status_code == 200:
            data = response.json()
            df = pd.DataFrame(data)
            df.to_csv('cri-cra2.csv', index=False)
            return df

    except json.JSONDecodeError:
        return response.text

