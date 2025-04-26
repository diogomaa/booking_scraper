
import os
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HOTEIS_CSV = os.path.join(BASE_DIR, "hoteis.csv")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

options = Options()
options.add_argument("--start-maximized")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

df = pd.read_csv(HOTEIS_CSV)
dados = []

for i, row in df.iterrows():
    nome = row["nome"]
    link = row["link"]

    print(f"🏨 {i+1}/{len(df)} - {nome}")
    try:
        driver.get(link)
        time.sleep(4)

        try:
            rating = driver.find_element(By.CSS_SELECTOR, '[data-testid="review-score-component"]').text
        except:
            rating = ""

        try:
            descricao = driver.find_element(By.CSS_SELECTOR, '[data-testid="property-description"]').text
        except:
            descricao = ""

        try:
            morada = driver.find_element(By.CSS_SELECTOR, '.a53cbfa6de.f17adf7576').text
        except:
            morada = ""

        try:
            destaques = driver.find_element(By.CSS_SELECTOR, '[data-testid="property-highlights"]').text
        except:
            destaques = ""

        try:
            comodidades = driver.find_element(By.CSS_SELECTOR, '[data-testid="property-most-popular-facilities-wrapper"]').text
        except:
            comodidades = ""

        
        try:
            info_alojamento_parts = []
            container = driver.find_elements(By.CSS_SELECTOR, '[data-testid="facility-group-container"]')
            blocos_extra = driver.find_elements(By.CSS_SELECTOR, '[data-testid="property-section--content"]')
            
            # Junta todos os textos do container principal
            info_alojamento_parts.extend([e.text for e in container if e.text.strip()])
            
            # Junta cada bloco extra com \n\n para maior legibilidade
            blocos_formatados = [e.text.strip() for e in blocos_extra if e.text.strip()]
            info_alojamento_parts.append("\n\n".join(blocos_formatados))
            
            info_alojamento = "\n\n".join(info_alojamento_parts)
        except:
            info_alojamento = ""


        try:
            categorias = driver.find_elements(By.CSS_SELECTOR, '[data-testid="review-subscore"]')
            categorias_avaliadas = "; ".join([c.text.replace("\n", " ").strip() for c in categorias])
        except:
            categorias_avaliadas = ""

        dados.append({
            "Nome": nome,
            "Link": link,
            "Rating Alojamento": rating,
            "Descricao": descricao,
            "Morada": morada,
            "Destaques da Propriedade": destaques,
            "Principais Comodidades": comodidades,
            "Informações do Alojamento": info_alojamento,
            "Categorias Avaliadas": categorias_avaliadas.strip().replace("; ;", "").replace("  ", "").replace(";", "\n")
        })

    except Exception as e:
        print(f"Erro no hotel {nome}: {e}")
        continue

driver.quit()
pd.DataFrame(dados).to_excel(os.path.join(OUTPUT_DIR, "hotel_info.xlsx"), index=False)
print("✅ FIM: hotel_info.xlsx criado")
