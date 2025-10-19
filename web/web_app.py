import time
import threading
import traceback
from selenium import webdriver
from path.paths import paths
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    WebDriverException,
    ElementNotInteractableException,
    JavascriptException,
    StaleElementReferenceException
)
from utils.Produtos import Produto
from processos.process_web import (
    expand_shadow_element, shadow_button, shadow_input, wait_for_element, click_element,wait_for_click, normal_input,
    button, acessar_valor, tentar_alterar_valor, processar_arquivo, shadow_input_quant, confirma_valor_quant
)

# Variável global para rastrear o número de tentativas
tentativas = 0
limite_tentativas = 3
# Variáveis globais de controle
monitoring = True
connection_successful = False
filial_selector = paths["filial_container"]
unidade_selector = paths["enter_unidade"]
data_selector = paths["data_container"]
amb_selector = paths["ambiente_container"]
cnpj_selector = paths["cnpj_container"]
input_pesquisa = paths["pesquisa_cnpj"]
filial_unidade = paths["confirma_unidade"]
btn_filial_unidade = paths["btn_unidade"]
btn_ok_cnpj = paths["btn_ok_cnpj"]
menu_pagto = paths["pesquisa_pagto"]
btn_ok_pagto_nat = paths["btn_ok_pagto_nat"]
unidades = ['0102', '0103', '0104']

def configurar_driver():
    """
    Configura e retorna o WebDriver para o Chrome.
    """
# Configurações do navegador
    chrome_options = Options()
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_argument("--ignore-ssl-errors")
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--disable-site-isolation-trials")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--start-maximized")  # Tela cheia
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    return driver

def abrir_site(driver, url):
    """
    Inicializa o navegador, acessa o site especificado e realiza interações iniciais necessárias.
    """
    try:
        driver.get(url)
        print(f"Site acessado: {url}")
        # Lógica para interagir com elementos na página
        return True
    except Exception as e:
        print(f"Erro ao abrir o site: {e}")
        return False

def fechar_site(driver):
    """
    Fecha o navegador, encerra o site especificado e realiza interações finais necessárias.
    """
    global monitoring
    monitoring = False
    driver.quit()

def iniciar_driver(produtos):
    """
    Inicia o WebDriver, acessa o site e executa o processo principal.
    Tenta novamente até 10 vezes em caso de erro.
    """
    max_tentativas = 10
    tentativa = 1

    while tentativa <= max_tentativas:
        print(f"\n🔄 Tentativa {tentativa}/{max_tentativas} de iniciar o processo...")
        driver = None

        try:
            driver = configurar_driver()
            url = "https://kairoscomercio136240.protheus.cloudtotvs.com.br:4010/webapp/"

            site_aberto = abrir_site(driver, url)
            if not site_aberto:
                raise Exception("Falha ao abrir o site.")

            print("✅ Site acessado com sucesso, prosseguindo com a lógica...")
            sucesso = main_process(driver, url, produtos)
            if sucesso:
                print("✅ Processamento concluído com sucesso.")
                if driver:
                    try:
                        driver.quit()
                        print("🛑 Driver finalizado.")
                    except Exception as e:
                        print(f"⚠️ Erro ao finalizar driver: {e}")

                return  # Sai do loop com sucesso

            else:
                print(f"❌ Erro na tentativa {tentativa}: {e}")
                tentativa += 1
                time.sleep(3)

        except Exception as e:
            print(f"❌ Erro na tentativa {tentativa}: {e}")
            tentativa += 1
            time.sleep(3)  # Pequena pausa antes de tentar novamente
            
    print("\n🚫 Todas as tentativas falharam. Processo abortado.")
    return None

def monitor_connection_thread(driver, url, stop_monitoring):
    """
    Inicia a thread de monitoramento da conexão.
    """
    monitor_thread = threading.Thread(target=monitor_connection, args=(driver, url, stop_monitoring))
    monitor_thread.start()
    return monitor_thread

def monitor_connection(driver, url, stop_monitoring, max_attempts=5, check_interval=5):
    """
    Monitora a conexão em segundo plano e retenta se houver erro.
    Para a thread se `stop_monitoring` for acionado.
    """
    global connection_successful
    attempt = 0

    while not stop_monitoring.is_set() and attempt < max_attempts and not connection_successful:
        try:
            print(f"[Monitor] Tentativa {attempt + 1} de {max_attempts} para acessar {url}...")

            # Aguarda a página carregar um elemento essencial
            wait_for_element(driver, By.CSS_SELECTOR, "wa-dialog.startParameters")
            print("[Monitor] Conexão bem-sucedida!")
            connection_successful = True
            return  # Sai da função ao conectar com sucesso

        except Exception as e:
            print(f"[Monitor] Erro ao tentar conectar: {e}")
            attempt += 1
            time.sleep(check_interval)

    if not connection_successful:
        print("[Monitor] Falha ao conectar após todas as tentativas.")

def fechar_iframe(driver):
    """
    Função para fechar o iframe acessado voltando para o documento principal do contexto.
    """
    try:
        driver.switch_to.default_content()
        print("Contexto retornado para o documento principal.")
    except Exception as e:
        print(f"Erro ao fechar o iframe: {e}")

def process_shadow_dom(driver):
    """
    Processa interações no Shadow DOM para clicar no botão OK e localizar outros elementos.
    """
    print("Selecionando tipo de ambiente no servidor...")

    # Localiza o combobox dentro do Shadow DOM
    wa_combo_box = wait_for_element(
        driver, 
        By.CSS_SELECTOR, 
        'wa-dialog.startParameters > fieldset[id="fieldsetEnv"] > wa-combobox[id="selectEnv"]'
    )
    shadow_combo_box = expand_shadow_element(driver, wa_combo_box)
    select_element = shadow_combo_box.find_element(By.CSS_SELECTOR, "select")

    # Opção desejada
    desired_value = "czls4f_prod"
    desired_option = select_element.find_element(By.CSS_SELECTOR, f"option[value='{desired_value}']")

    # Opção atual selecionada
    current_option = select_element.find_element(By.CSS_SELECTOR, "option:checked")
    current_value = current_option.get_attribute("value")

    if current_value == desired_value:
        print(f"\nAmbiente '{desired_value}' já está selecionado, não será alterado.")
    else:
        desired_option.click()
        print(f"\nAmbiente '{desired_value}' selecionado.")

    time.sleep(1)

    print("\nAguardando wa-dialog...")
    shadow_button(driver, "wa-dialog.startParameters", "wa-button[title='Botão confirmar']")

    time.sleep(3)

def locate_and_access_iframe(driver):
    """
    Localiza o iframe dentro do Shadow DOM e alterna para ele.
    """
    print("Aguardando próximo wa-dialog...")
    
    wa_dialog_2 = wait_for_element(driver, By.ID, 'COMP3000')
    print("Acessando o wa-image...")
    
    wa_image_1 = wait_for_element(wa_dialog_2, By.ID, 'COMP3008')
    print("Acessando o wa-webview...")
    
    wa_webview_1 = wait_for_element(wa_image_1, By.ID, 'COMP3010')
    print("Acessando shadow root do webview...")
    
    shadow_root_2 = expand_shadow_element(driver, wa_webview_1)
    print("Acessando o iframe dentro do shadowRoot...")
    iframe = wait_for_element(shadow_root_2, By.CSS_SELECTOR, 'iframe[src*="kairoscomercio136240.protheus.cloudtotvs.com.br"]')

    if iframe:
        print("Iframe localizado com sucesso.")
        driver.switch_to.frame(iframe)
        print("Dentro do iframe.")
    else:
        raise Exception("Iframe não encontrado.")

def perform_login(driver, login, password):
    """
    Preenche os campos de login e senha e realiza a autenticação.
    """
    try:
        normal_input(driver, '.po-field-container-content', '[name="login"]', login, "User")
        
        normal_input(driver, '[name="password"]', 'input[name="password"]', password, "Password")

        time.sleep(2)
        button_enter = wait_for_element(driver, By.CSS_SELECTOR, 'po-button')
        click_element(button_enter, (By.CSS_SELECTOR, "button.po-button[p-kind=primary]"))
        print("Botão Entrar clicado com sucesso!")
        time.sleep(2)
    except Exception as e:
        print(f"Erro durante o login: {e}")

def abrir_menu_unidade(driver):
    """
    Função inicial para inserir a data e filial correta que deseja(Tela inicial).
    """
    print("Acessando ambiente 02...")
    
    container_amb = wait_for_element(driver, By.CSS_SELECTOR, amb_selector)
    WebDriverWait(driver, 20).until(EC.visibility_of(container_amb))
    amb_field = wait_for_click(container_amb, By.CSS_SELECTOR, 'input')
    
    # Garantir que o elemento esteja visível
    driver.execute_script("arguments[0].scrollIntoView(true);", amb_field)
    normal_input(driver, amb_selector, 'input', '2', "Ambiente")
    
    time.sleep(0.5)
    
    amb_field.send_keys(Keys.TAB)

    print("Acesso Concluído.")

    time.sleep(0.3)
    # Procurando e clicando no botão
    container_but = wait_for_element(driver, By.CSS_SELECTOR, unidade_selector)

    ActionChains(driver).move_to_element(container_but).perform()
    print("Busca do container do botão Enter completa.")
    click_element(container_but, (By.CSS_SELECTOR, "button"))
    print("Botão de entrar na unidade clicado com sucesso!")

    fechar_iframe(driver)

    time.sleep(10)

def rotina_produtos(driver):
    """
    Função que após apertar o botão de Favoritos acessa a rotina Pedidos de Venda.
    """
    print("Buscando pesquisa de rotina.")
    campo_rotina = wait_for_element(driver, By.CSS_SELECTOR, 'wa-panel[id="COMP3053"] > wa-text-input[id="COMP3056"]')
    shadow_input(driver, 'wa-panel[id="COMP3053"] > wa-text-input[id="COMP3056"]', "Produtos")

    valor_atual = acessar_valor(campo_rotina).strip()
    print(f"Valor atual do campo: {valor_atual}")

    if valor_atual != "Produtos":
        if tentar_alterar_valor(driver, campo_rotina, "Produtos", 'wa-panel[id="COMP3053"] > wa-text-input[id="COMP3056"]'):
            print("Valor alterado com sucesso.")
        else:
            print("Falha ao alterar valor")
    else:
        print("O valor já está correto, nenhuma alteração necessária.")

    print("Rotina inserida com sucesso.")

    print("Buscando botão...")
    input_rotina = wait_for_element(driver, By.CSS_SELECTOR, 'wa-panel[id="COMP3053"] > wa-text-input[id="COMP3056"]')
    btn_pesq = wait_for_element(driver, By.CSS_SELECTOR, 'button.button-image')
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn_pesq)
    time.sleep(1)
    click_element(input_rotina, (By.CSS_SELECTOR, 'button.button-image'))

    shadow_button(driver, 'wa-menu-item[id="COMP4523"]', '.caption[title="Compras (2)"]')
    shadow_button(driver, 'wa-menu-item[id="COMP4519"]', '.caption[title="Cadastros (9)"]')
    shadow_button(driver, 'wa-menu-item[id= "COMP4521"]', '.caption[title="Produtos"]')

    print("Buscando segunda tela de validação...")
    print("Abrindo wa-dialog do menu...")

def definir_grupo(driver, produtos):
    print("Aguardando filtro para grupo...")
    wait_for_element(driver, By.CSS_SELECTOR, 'wa-panel[id="COMP6001"] > wa-text-input[id="COMP6003"]')
    print("Carregado.")
    for produto in produtos:
        if produto['GRUPO']:
            shadow_input(driver, 'wa-panel[id="COMP6001"] > wa-text-input[id="COMP6003"]', produto['GRUPO'])
            print("Confirmando valor...")
            shadow_button(driver, 'wa-panel[id="COMP6004"] > wa-button[id="COMP6006"]', 'button')

            return

def apertar_incluir(driver):
    """
    Função para apertar o botão de incluir em Pedidos de Venda
    """
    print("Buscando wa-panel da rotina de Produtos...")
    try:
        wait_for_element(driver, By.ID, 'COMP4586')
    except Exception as e:
        print(f"ERRO NO IDENTIFICADOR 1: {e}")
        try:
            print("\nIniciando busca de novo ID.")
            wait_for_element(driver, By.ID, 'COMP4591')
        except Exception as e:
            print(f"ERRO NO ÚLTIMO IDENTIFICADOR: {e}")

    print("Tela carregada com sucesso.")
    time.sleep(5)

    print("Buscando botão de incluir...")
    for i in range(0,5):    
        try:
            print(f"Tentativa: {i+1}")
            try:
                btn_incluir = wait_for_click(driver, By.ID, 'COMP4587')
                print("Botão encontrado e expandindo shadow DOM...")
                shadow_root_btn = expand_shadow_element(driver, btn_incluir)
                button(driver, shadow_root_btn)
                time.sleep(2)
            except Exception as e:
                btn_incluir = wait_for_click(driver, By.ID, 'COMP4592')
                print("Botão encontrado e expandindo shadow DOM...")
                shadow_root_btn = expand_shadow_element(driver, btn_incluir)
                button(driver, shadow_root_btn)
                time.sleep(2)
            
            if wait_for_element(driver, By.ID, 'COMP6000', timeout=30):
                print("Botão clicado com sucesso.")
                print("Aberto.")
                break
            else:
                print(f"Erro na tentativa: {i+1}, tentando novamente...")
        except Exception as e:
            print(f"Erro: {e}")

def busca_produto(driver, produtos):
    for produto in produtos:
        print("\nPesquisando produto...")
        string_codigo = str(produto['Codigo']).strip()
        field_produto = wait_for_element(driver, By.CSS_SELECTOR, 'wa-panel[id="COMP4526"] > wa-text-input[id="COMP4528"]')
        shadow_input(driver, 'wa-panel[id="COMP4526"] > wa-text-input[id="COMP4528"]', string_codigo)
        time.sleep(1)
        valor_atual = acessar_valor(field_produto).strip()
        confirma_valor(driver, valor_atual, string_codigo, field_produto, 'wa-panel[id="COMP4526"] > wa-text-input[id="COMP4528"]')
        
        print("Apertando na pesquisa...")
        shadow_button(driver, 'wa-panel[id="COMP4526"] > wa-button[id="COMP4529"]', 'button')
        time.sleep(5)

        print("\nAguardando tabela...")
        wa_tgrid = wait_for_element(driver, By.CSS_SELECTOR, 'wa-dialog[id="COMP4500"] > wa-tgrid[id="COMP4513"]')
        shadow_tgrid = expand_shadow_element(driver, wa_tgrid)

        codigo = wait_for_element(shadow_tgrid, By.CSS_SELECTOR, 'table > tbody > tr#\\30 > td#\\31 > div > label')
        codigo_texto = codigo.text.strip()
        print(f"Código: {codigo_texto}")
        
        time.sleep(2)
        
        if string_codigo == codigo_texto:
            print("Produto pesquisado com sucesso.")
        else:
            print("Produto não condiz com o desejado.")
        
        unid = wait_for_element(shadow_tgrid, By.CSS_SELECTOR, 'table > tbody > tr#\\30 > td#\\35 > div > label')
        unid_texto = unid.text.strip()
        print(f"\nUnidade: {unid_texto}")

        time.sleep(1)

        if unid_texto == 'UN':
            print("\nNecessário alterar tipo.")
            altera_tipo(driver)
            time.sleep(0.5)
            processar_arquivo(codigo_texto)
        else:
            print("\nPassando para o próximo produto.")

def altera_tipo(driver):

    while True:
        try:
            print("\nAbrindo confirmação de atributos...")
            wait_for_element(driver, By.CSS_SELECTOR, 'wa-panel[id="COMP4586"] > wa-button[id="COMP4588"]')
            print("Botão encontrado.")
            shadow_button(driver, 'wa-panel[id="COMP4586"] > wa-button[id="COMP4588"]', 'button')

            print("\nAguardando tabela com unidade...")
            wait_for_element(driver, By.CSS_SELECTOR, 'wa-panel[id="COMP6029"] > wa-text-input[id="COMP6035"]', timeout=5)
            break
        except TimeoutException:
            print("\nTimeout ao esperar pelo elemento! Tentando novamente...")

    print("\nBuscando campo de UNIDADE.")
    campo_rotina = wait_for_element(driver, By.CSS_SELECTOR, 'wa-panel[id="COMP6029"] > wa-text-input[id="COMP6035"]')
    shadow_input(driver, 'wa-panel[id="COMP6029"] > wa-text-input[id="COMP6035"]', "PC")

    valor_atual = acessar_valor(campo_rotina).strip()
    print(f"Valor atual do campo: {valor_atual}")

    if valor_atual != "PC":
        if tentar_alterar_valor(driver, campo_rotina, "PC", 'wa-panel[id="COMP6029"] > wa-text-input[id="COMP6035"]'):
            print("Valor alterado com sucesso.")
        else:
            print("Falha ao alterar valor")
    else:
        print("O valor já está correto, nenhuma alteração necessária.")
    
    time.sleep(2)
    
    wait_for_click(driver, By.CSS_SELECTOR, 'wa-panel[id="COMP6550"] > wa-button[id="COMP6552"]')

    shadow_button(driver, 'wa-panel[id="COMP6550"] > wa-button[id="COMP6552"]', 'button')

    time.sleep(0.5)

    wait_for_click(driver, By.CSS_SELECTOR, 'wa-panel[id="COMP7509"] > wa-button[id="COMP7511"]')
    shadow_button(driver, 'wa-panel[id="COMP7509"] > wa-button[id="COMP7511"]', 'button')

    time.sleep(2)

# ==============================================================================
# FUNÇÃO AUXILIAR 1: CONFIRMAÇÃO DE VALOR
# ==============================================================================
def confirma_valor(driver, valor_atual, valor_desejado, wa_panel_element, seletor_input, max_tentativas=3):
    """
    Verifica se o valor de um campo foi alterado corretamente e tenta corrigi-lo se não foi.
    Levanta um erro se não conseguir confirmar a alteração após várias tentativas.
    """
    # Normaliza os valores para uma comparação segura, tratando strings e maiúsculas
    valor_atual = str(valor_atual).strip().upper()
    valor_desejado = str(valor_desejado).strip().upper()

    if valor_atual == valor_desejado:
        print(f"-> Valor '{valor_desejado}' confirmado com sucesso.")
        return

    # Se o valor não estiver correto, inicia as tentativas de correção
    for tentativa in range(1, max_tentativas + 1):
        print(f"[AVISO] Valor incorreto detectado. Tentativa {tentativa}/{max_tentativas} para corrigir...")
        print(f"  - Esperado: '{valor_desejado}'")
        print(f"  - Encontrado: '{valor_atual}'")
        
        shadow_input(driver, seletor_input, valor_desejado) # Tenta inserir o valor novamente
        time.sleep(0.5)
        
        valor_atual = str(acessar_valor(wa_panel_element)).strip().upper()
        
        if valor_atual == valor_desejado:
            print(f"-> Correção bem-sucedida. Valor '{valor_desejado}' confirmado.")
            return

    raise Exception(f"ERRO CRÍTICO: Não foi possível definir o valor do campo para '{valor_desejado}'.")

# ==============================================================================
# FUNÇÃO AUXILIAR 2: SALVAMENTO ROBUSTO
# ==============================================================================
def _salvar_e_confirmar_robusto(driver, max_tentativas=5):
    """
    Tenta salvar e confirmar o produto de forma agressiva em um loop.
    Só para quando os painéis de salvar e de confirmar desaparecerem.
    """
    print("Clicando no botão 'Salvar'...")
    shadow_button(driver, 'wa-panel[id="COMP6550"] > wa-button[id="COMP6554"]', 'button')
    
    for tentativa in range(1, max_tentativas + 1):
        print(f"\n--- Tentativa {tentativa}/{max_tentativas} para Salvar e Confirmar ---")
        try:
            print("Clicando no botão 'Confirmar' final...")
            wait_for_element(driver, By.CSS_SELECTOR, 'wa-panel[id="COMP7509"]')
            shadow_button(driver, 'wa-panel[id="COMP7509"] > wa-button[id="COMP7511"]', 'button')

            print("Aguardando o fechamento das janelas de salvamento...")
            wait = WebDriverWait(driver, 5)
            
            wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, 'wa-panel[id="COMP7509"] > wa-button[id="COMP7511"]')))

            print(">>> SUCESSO: Produto salvo e janelas de confirmação fechadas.")
            return

        except (TimeoutException, StaleElementReferenceException) as e:
            print(f"[AVISO] Falha na tentativa {tentativa}: {str(e).splitlines()[0]}")
            print("Tentando novamente...")
            try:
                print("Clicando no botão 'Salvar'...")
                shadow_button(driver, 'wa-panel[id="COMP6550"] > wa-button[id="COMP6554"]', 'button')
            except:
                pass
            time.sleep(2)
            
    raise Exception("ERRO CRÍTICO: Não foi possível confirmar o salvamento do produto após múltiplas tentativas.")

# ==============================================================================
# FUNÇÃO PRINCIPAL: INSERIR PRODUTO (COMPLETA)
# ==============================================================================
def inserir_produto(driver, produtos, it_prod):
    """
    Função principal de inserção, agora usando as funções auxiliares para robustez e clareza.
    """
    idx_inicial = it_prod.obter_valor("ultimo_idx")
    total_produtos = len(produtos)
    
    print(f"Iniciando inserção em lote. Produtos restantes: {total_produtos - idx_inicial}")

    for idx in range(idx_inicial, total_produtos):
        produto_atual = produtos[idx]
        print(f"\n--- Processando produto {idx + 1}/{total_produtos} (Grupo: {produto_atual['GRUPO']}) ---")

        wait_for_element(driver, By.CSS_SELECTOR, 'wa-panel[id="COMP6029"]')
        
        # --- Preenchimento e Confirmação de cada campo ---

        # Grupo
        seletor = 'wa-panel[id="COMP6029"] > wa-text-input[id="COMP6030"]'
        elemento = wait_for_element(driver, By.CSS_SELECTOR, seletor)
        shadow_input(driver, seletor, produto_atual['GRUPO'])
        confirma_valor(driver, acessar_valor(elemento), produto_atual['GRUPO'], elemento, seletor)

        # Descrição
        seletor = 'wa-panel[id="COMP6029"] > wa-text-input[id="COMP6032"]'
        elemento = wait_for_element(driver, By.CSS_SELECTOR, seletor)
        shadow_input(driver, seletor, produto_atual['DESCRICAO'])
        confirma_valor(driver, acessar_valor(elemento), produto_atual['DESCRICAO'], elemento, seletor)
        
        # Descrição Específica
        seletor = 'wa-panel[id="COMP6029"] > wa-text-input[id="COMP6033"]'
        elemento = wait_for_element(driver, By.CSS_SELECTOR, seletor)
        shadow_input(driver, seletor, produto_atual['DESCRICAO'])
        confirma_valor(driver, acessar_valor(elemento), produto_atual['DESCRICAO'], elemento, seletor)

        # Tipo
        seletor = 'wa-panel[id="COMP6029"] > wa-text-input[id="COMP6034"]'
        elemento = wait_for_element(driver, By.CSS_SELECTOR, seletor)
        shadow_input(driver, seletor, produto_atual['TIPO'])
        confirma_valor(driver, acessar_valor(elemento), produto_atual['TIPO'], elemento, seletor)
        
        # Unidade
        seletor = 'wa-panel[id="COMP6029"] > wa-text-input[id="COMP6035"]'
        elemento = wait_for_element(driver, By.CSS_SELECTOR, seletor)
        shadow_input(driver, seletor, produto_atual['UNIDADE'])
        confirma_valor(driver, acessar_valor(elemento), produto_atual['UNIDADE'], elemento, seletor)
        
        # Armazém
        seletor = 'wa-panel[id="COMP6029"] > wa-text-input[id="COMP6036"]'
        elemento = wait_for_element(driver, By.CSS_SELECTOR, seletor)
        shadow_input(driver, seletor, produto_atual['ARMAZEM'])
        confirma_valor(driver, acessar_valor(elemento), produto_atual['ARMAZEM'], elemento, seletor)
        
        # NCM
        seletor = 'wa-panel[id="COMP6029"] > wa-text-input[id="COMP6037"]'
        elemento = wait_for_element(driver, By.CSS_SELECTOR, seletor)
        shadow_input(driver, seletor, str(produto_atual['NCM'])) # Você mencionou uma multiplicação por 8, ajuste se necessário
        confirma_valor(driver, acessar_valor(elemento), str(produto_atual['NCM']).replace(".", ""), elemento, seletor)

        # Preço de Venda (usando a função específica para quantidade)
        seletor = 'wa-panel[id="COMP6029"] > wa-text-input[id="COMP6041"]'
        elemento = wait_for_element(driver, By.CSS_SELECTOR, seletor)
        shadow_input_quant(driver, seletor, produto_atual['PRECO VENDA'])
        valor_atual_formatado = f"{float(acessar_valor(elemento)):.2f}".replace(".", ",")
        confirma_valor_quant(driver, valor_atual_formatado, produto_atual['PRECO VENDA'], elemento, seletor)

        # Código do Fornecedor
        seletor = 'wa-panel[id="COMP6029"] > wa-text-input[id="COMP6046"]'
        elemento = wait_for_element(driver, By.CSS_SELECTOR, seletor)
        shadow_input(driver, seletor, produto_atual['COD FOR'])
        confirma_valor(driver, acessar_valor(elemento), produto_atual['COD FOR'], elemento, seletor)
        
        # Código do Fornecedor CLI
        seletor = 'wa-panel[id="COMP6029"] > wa-text-input[id="COMP6063"]'
        elemento = wait_for_element(driver, By.CSS_SELECTOR, seletor)
        shadow_input(driver, seletor, produto_atual['COD PRO CLI'])
        confirma_valor(driver, acessar_valor(elemento), produto_atual['COD PRO CLI'], elemento, seletor)
        
        # Unidade de Medida CLI
        seletor = 'wa-panel[id="COMP6029"] > wa-text-input[id="COMP6064"]'
        elemento = wait_for_element(driver, By.CSS_SELECTOR, seletor)
        shadow_input(driver, seletor, produto_atual['UNIDADE.1'])
        confirma_valor(driver, acessar_valor(elemento), produto_atual['UNIDADE.1'], elemento, seletor)

        # --- LÓGICA DE SALVAMENTO ---
        _salvar_e_confirmar_robusto(driver)

        # Atualiza o índice para o próximo produto
        it_prod.atualizar_valor("ultimo_idx", idx + 1)

    print("\nFechando menu...")
    wait_for_element(driver, By.CSS_SELECTOR, 'wa-panel[id="COMP6550"] > wa-button[id="COMP6553"]')
    shadow_button(driver, 'wa-panel[id="COMP6550"] > wa-button[id="COMP6553"]', 'button')
    print("Menu fechado.")

def inicializar_sistema(driver):
    """ Realiza login e inicializações no sistema. """
    process_shadow_dom(driver)
    locate_and_access_iframe(driver)
    perform_login(driver, "000160", "PLTF16010506")
    abrir_menu_unidade(driver)

def main_process(driver, url, produtos):
    """
    Gerencia o fluxo principal do processo para múltiplas notas, agora com integração ao banco de dados SQLite.
    O mês e ano da tabela são passados como parâmetro, e a data em abrir_menu_unidade é baseada na primeira nota com status "Encontrado".
    """
    global connection_successful, monitoring

    stop_monitoring = threading.Event()
    monitor_thread = monitor_connection_thread(driver, url, stop_monitoring)

    try:
        print("Iniciando o código principal...")

        # Aguardar conexão
        while not connection_successful:
            print("Aguardando conexão...")
            time.sleep(1)

        if connection_successful:
            print("Conexão estabelecida. Iniciando processamento!")

            # Inicializar sistema
            inicializar_sistema(driver)

            # Executar fluxo principal
            rotina_produtos(driver)
            
            shadow_button(
            driver, 
            'wa-dialog[id="COMP4500"] > wa-panel[id="COMP4503"] > wa-panel[id="COMP4504"] > wa-panel[id="COMP4520"] > wa-button[id="COMP4522"]', 
            'button')

            instan_prod = Produto("register/index_prod.json")

            definir_grupo(driver, produtos)
            
            # busca_produto(driver, produtos)

            apertar_incluir(driver)
            time.sleep(7)

            inserir_produto(driver, produtos, instan_prod)

            print("\nAlteração de produtos concluída.")

            time.sleep(15)

        else:
            print("Conexão não estabelecida. Verifique a lógica de monitoramento.")

    except (NoSuchElementException, ElementNotInteractableException, TimeoutException, JavascriptException, WebDriverException) as e:
        msg = f"Erro Selenium: {e}"
        print(msg)
        print(traceback.format_exc())  

        return False
    except Exception as e:
        msg = f"Erro no processo principal: {e}"
        print(msg)
        print(traceback.format_exc())

        return False
    finally:
        stop_monitoring.set()
        monitor_thread.join()
        print("Finalizando driver e monitoramento.")