
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, ElementClickInterceptedException
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pandas as pd
import time
from pathlib import Path
import os
import json

# Configurações
options = Options()
options.add_argument("--start-maximized")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# Carregar CSV
df = pd.read_csv("hoteis.csv")

# Caminho de output
output_dir = Path("output")
output_dir.mkdir(exist_ok=True)
output_file = output_dir / "comentarios_final_temp.xlsx"

# Ficheiro de progresso
progresso_file = output_dir / "progress.json"
if progresso_file.exists():
    with open(progresso_file, "r", encoding="utf-8") as f:
        progresso = json.load(f)
        hotel_inicio = progresso.get("hotel_index", 0)
else:
    progresso = {}
    hotel_inicio = 0

# Estado inicial
comentarios_total = []
if output_file.exists():
    df_existente = pd.read_excel(output_file)
    comentarios_total = df_existente.to_dict(orient="records")

def guardar_excel(temp=True):
    final = output_dir / ("comentarios_final.xlsx" if not temp else "comentarios_final_temp.xlsx")
    pd.DataFrame(comentarios_total).to_excel(final, index=False)
    print(f"💾 Ficheiro guardado: {final.name}")

try:
    for idx, row in df.iloc[hotel_inicio:].iterrows():
        nome_hotel = row["nome"]
        url = row["link_reviews"]

        print(f"🏨 {hotel_inicio + idx + 1}/{len(df)} - {nome_hotel}")
        driver.get(url)

        time.sleep(4)

        try:
            WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
            ).click()
        except:
            pass

        pagina = 1
        while True:
            print(f"📄 A processar página {pagina}...")
            time.sleep(2)
            soup = BeautifulSoup(driver.page_source, "html.parser")

            try:
                ver_todos = driver.find_element(By.XPATH, '//button[contains(text(), "Ver todos os coment")]')
                if ver_todos.is_displayed():
                    ver_todos.click()
                    time.sleep(2)
            except:
                pass

            reviews = soup.select('[data-testid="review-card"]')
            if not reviews:
                print("⚠️ Nenhum review encontrado nesta página.")

            for review in reviews:
                try:
                    nome = review.select_one('[data-testid="review-avatar"] div[class^="a3332d"]')
                    nacionalidade = review.select_one('[data-testid="review-avatar"] span[class^="afac"]')
                    tipo_quarto = review.select_one('[data-testid="review-room-name"]')
                    noites = review.select_one('[data-testid="review-num-nights"]')
                    data = review.select_one('[data-testid="review-date"]')
                    score = review.select_one('[data-testid="review-score"]')
                    titulo = review.select_one('[data-testid="review-title"]')
                    positivo = review.select_one('[data-testid="review-positive-text"]')
                    negativo = review.select_one('[data-testid="review-negative-text"]')
                    tipo_viajante = review.select_one('[data-testid="review-traveler-type"]')
                    tipo_viajante = tipo_viajante.text.strip() if tipo_viajante else ""
                    data_reserva = review.select_one('[data-testid="review-stay-date"]')
                    data_reserva = data_reserva.text.strip() if data_reserva else ""

                    comentarios_total.append({
                        "Hotel": nome_hotel,
                        "Nome": nome.text.strip() if nome else "",
                        "Nacionalidade": nacionalidade.text.strip() if nacionalidade else "",
                        "Tipo de Quarto": tipo_quarto.text.strip().replace("·", "") if tipo_quarto else "",
                        "Nº de Noites": noites.text.strip() if noites else "",
                        "Data do Comentário": data.text.strip().replace("Data do comentário: ", "") if data else "",
                        "Pontuação": (
                            "10" if score and "10" in score.text.strip()
                            else score.text.strip().replace("Pontuado com ", "").replace(",", ".").split(".")[0] + ".0"
                        ) if score else "",
                        "Título": titulo.text.strip() if titulo else "",
                        "Comentário Positivo": positivo.text.strip() if positivo else "",
                        "Comentário Negativo": negativo.text.strip() if negativo else "",
                        "Tipo de Viajante": tipo_viajante,
                        "Data da Reserva": data_reserva
                    })
                except Exception as e:
                    print(f"⚠️ Erro ao extrair review: {e}")

            try:
                botao_proximo = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[aria-label="Página seguinte"]'))
                )
                if "disabled" in botao_proximo.get_attribute("class"):
                    print("📄 Não há mais páginas (botão desativado).")
                    break
                botao_proximo.click()
                pagina += 1
                time.sleep(2)
            except TimeoutException:
                print("📄 Não há mais páginas (sem botão).")
                break
            except ElementClickInterceptedException:
                print("⚠️ Clique bloqueado — clica manualmente e pressiona ENTER para continuar.")
                input()

        guardar_excel(temp=True)
        with open(progresso_file, "w", encoding="utf-8") as f:
            json.dump({"hotel_index": hotel_inicio + idx + 1}, f)

except KeyboardInterrupt:
    print("⛔ Interrompido — a guardar ficheiro temporário...")
    guardar_excel(temp=True)
    with open(progresso_file, "w", encoding="utf-8") as f:
        json.dump({"hotel_index": hotel_inicio + idx}, f)
    driver.quit()
    exit()

guardar_excel(temp=False)
print("🟢 Scraping concluído com sucesso.")
input("Pressiona ENTER para sair...")
driver.quit()
