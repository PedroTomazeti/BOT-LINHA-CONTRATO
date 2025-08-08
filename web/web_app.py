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
)
from utils.Produtos import Produto
from processos.process_web import (
    expand_shadow_element, shadow_button, shadow_input, wait_for_element, click_element,wait_for_click, normal_input,
    button, acessar_valor, tentar_alterar_valor, confirma_valor, processar_arquivo, shadow_input_quant, confirma_valor_quant
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
            driver.get(url)

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
    print("Aguardando wa-dialog...")
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

    amb_field.send_keys(Keys.TAB)

    print("Acesso Concluído.")
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
    wait_for_element(driver, By.ID, 'COMP4586')
    print("Tela carregada com sucesso.")
    time.sleep(5)

    print("Buscando botão de incluir...")
    for i in range(0,5):    
        try:
            print(f"Tentativa: {i+1}")
            btn_incluir = wait_for_element(driver, By.ID, 'COMP4587')
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

def inserir_produto(driver, produtos, it_prod):
    idx = it_prod.obter_valor("ultimo_idx")
    list_tam = len(produtos)

    restantes = list_tam - idx

    for i in range(restantes):
        idx = it_prod.obter_valor("ultimo_idx")
        wait_for_element(driver, By.CSS_SELECTOR, 'wa-panel[id="COMP6029"]')
        
        print("\nIncluindo Grupo...")
        wa_panel = wait_for_element(driver, By.CSS_SELECTOR, 'wa-panel[id="COMP6029"] > wa-text-input[id="COMP6030"]')
        shadow_input(driver, 'wa-panel[id="COMP6029"] > wa-text-input[id="COMP6030"]', produtos[idx]['GRUPO'])
        print("Incluído.")
        
        valor_atual = acessar_valor(wa_panel).strip()  # Remove espaços extras
        print(f"Valor atual do campo: {valor_atual}")
        
        valor_desejado = str(produtos[idx]['GRUPO']).strip()

        confirma_valor(driver, valor_atual, valor_desejado, wa_panel, 'wa-panel[id="COMP6029"] > wa-text-input[id="COMP6030"]')
        
        print("\nIncluindo Descrição...")
        wa_panel = wait_for_element(driver, By.CSS_SELECTOR, 'wa-panel[id="COMP6029"] > wa-text-input[id="COMP6032"]')
        shadow_input(driver, 'wa-panel[id="COMP6029"] > wa-text-input[id="COMP6032"]', produtos[idx]['DESCRICAO'])
        print("Incluído.")

        valor_atual = acessar_valor(wa_panel).strip()  # Remove espaços extras
        print(f"Valor atual do campo: {valor_atual}")
        
        valor_desejado = str(produtos[idx]['DESCRICAO']).strip().upper()

        confirma_valor(driver, valor_atual, valor_desejado, wa_panel, 'wa-panel[id="COMP6029"] > wa-text-input[id="COMP6032"]')

        print("\nIncluindo Descrição Específica...")
        wa_panel = wait_for_element(driver, By.CSS_SELECTOR, 'wa-panel[id="COMP6029"] > wa-text-input[id="COMP6033"]')
        shadow_input(driver, 'wa-panel[id="COMP6029"] > wa-text-input[id="COMP6033"]', produtos[idx]['DESCRICAO'])
        print("Incluído.")

        valor_atual = acessar_valor(wa_panel).strip()  # Remove espaços extras
        print(f"Valor atual do campo: {valor_atual}")
        
        valor_desejado = str(produtos[idx]['DESCRICAO']).strip().upper()

        confirma_valor(driver, valor_atual, valor_desejado, wa_panel, 'wa-panel[id="COMP6029"] > wa-text-input[id="COMP6033"]')
        
        print("\nIncluindo Tipo...")
        wa_panel = wait_for_element(driver, By.CSS_SELECTOR, 'wa-panel[id="COMP6029"] > wa-text-input[id="COMP6034"]')
        shadow_input(driver, 'wa-panel[id="COMP6029"] > wa-text-input[id="COMP6034"]', produtos[idx]['TIPO'])
        print("Incluído.")

        valor_atual = acessar_valor(wa_panel).strip()  # Remove espaços extras
        print(f"Valor atual do campo: {valor_atual}")
        
        valor_desejado = str(produtos[idx]['TIPO']).strip().upper()

        confirma_valor(driver, valor_atual, valor_desejado, wa_panel, 'wa-panel[id="COMP6029"] > wa-text-input[id="COMP6034"]')

        print("\nIncluindo Unidade...")
        wa_panel = wait_for_element(driver, By.CSS_SELECTOR, 'wa-panel[id="COMP6029"] > wa-text-input[id="COMP6035"]')
        shadow_input(driver, 'wa-panel[id="COMP6029"] > wa-text-input[id="COMP6035"]', produtos[idx]['UNIDADE'])
        print("Incluído.")

        valor_atual = acessar_valor(wa_panel).strip()  # Remove espaços extras
        print(f"Valor atual do campo: {valor_atual}")
        
        valor_desejado = str(produtos[idx]['UNIDADE']).strip().upper()

        confirma_valor(driver, valor_atual, valor_desejado, wa_panel, 'wa-panel[id="COMP6029"] > wa-text-input[id="COMP6035"]')

        print("\nIncluindo Armazem...")    
        wa_panel = wait_for_element(driver, By.CSS_SELECTOR, 'wa-panel[id="COMP6029"] > wa-text-input[id="COMP6036"]')
        shadow_input(driver, 'wa-panel[id="COMP6029"] > wa-text-input[id="COMP6036"]', produtos[idx]['ARMAZEM'])
        print("Incluído.")

        valor_atual = acessar_valor(wa_panel).strip()  # Remove espaços extras
        print(f"Valor atual do campo: {valor_atual}")
        
        valor_desejado = str(produtos[idx]['ARMAZEM']).strip()

        confirma_valor(driver, valor_atual, valor_desejado, wa_panel, 'wa-panel[id="COMP6029"] > wa-text-input[id="COMP6036"]')

        print("\nIncluindo NCM...")
        wa_panel = wait_for_element(driver, By.CSS_SELECTOR, 'wa-panel[id="COMP6029"] > wa-text-input[id="COMP6037"]')
        shadow_input(driver, 'wa-panel[id="COMP6029"] > wa-text-input[id="COMP6037"]', str(produtos[idx]['NCM']) * 8)
        print("Incluído.")

        valor_atual = acessar_valor(wa_panel).strip()  # Remove espaços extras
        print(f"Valor atual do campo: {valor_atual}")
        
        valor_desejado = str(produtos[idx]['NCM']).replace(".", "").strip()

        confirma_valor(driver, valor_atual, valor_desejado, wa_panel, 'wa-panel[id="COMP6029"] > wa-text-input[id="COMP6037"]')

        print("\nIncluindo Preço de venda...")
        print(f"Preço: R$ {produtos[idx]['PRECO VENDA']}")
        
        wa_panel = wait_for_element(driver, By.CSS_SELECTOR, 'wa-text-input[id="COMP6041"]')
        shadow_input_quant(driver, 'wa-panel[id="COMP6029"] > wa-text-input[id="COMP6041"]', produtos[idx]['PRECO VENDA'])
        print("Incluído.")

        valor_atual = acessar_valor(wa_panel)
        print(f"Valor atual do campo: {valor_atual}")

        # Converter 'valor_atual' para float, depois formatá-lo com duas casas decimais e vírgula
        valor_atual_formatado = f"{float(valor_atual):.2f}".replace(".", ",")

        print(f"Valor atual formatado: {valor_atual}")

        confirma_valor_quant(driver, valor_atual_formatado, produtos[idx]['PRECO VENDA'], wa_panel, 'wa-panel[id="COMP6029"] > wa-text-input[id="COMP6041"]')

        print("\nIncluindo Código do fornecedor...")
        wa_panel = wait_for_element(driver, By.CSS_SELECTOR, 'wa-text-input[id="COMP6046"]')
        shadow_input(driver, 'wa-panel[id="COMP6029"] > wa-text-input[id="COMP6046"]', produtos[idx]['COD FOR'])
        print("Incluído.")

        valor_atual = acessar_valor(wa_panel).strip()  # Remove espaços extras
        print(f"Valor atual do campo: {valor_atual}")
        
        valor_desejado = str(produtos[idx]['COD FOR']).strip()

        confirma_valor(driver, valor_atual, valor_desejado, wa_panel, 'wa-panel[id="COMP6029"] > wa-text-input[id="COMP6046"]')

        print("\nIncluindo Código do fornecedor CLI...")
        wa_panel = wait_for_element(driver, By.CSS_SELECTOR, 'wa-text-input[id="COMP6063"]')
        shadow_input(driver, 'wa-panel[id="COMP6029"] > wa-text-input[id="COMP6063"]', produtos[idx]['COD PRO CLI'])
        print("Incluído.")

        valor_atual = acessar_valor(wa_panel).strip()  # Remove espaços extras
        print(f"Valor atual do campo: {valor_atual}")
        
        valor_desejado = str(produtos[idx]['COD PRO CLI']).strip()

        confirma_valor(driver, valor_atual, valor_desejado, wa_panel, 'wa-panel[id="COMP6029"] > wa-text-input[id="COMP6063"]')

        print("\nIncluindo Unidade de medida CLI...")
        wa_panel = wait_for_element(driver, By.CSS_SELECTOR, 'wa-text-input[id="COMP6064"]')
        shadow_input(driver, 'wa-panel[id="COMP6029"] > wa-text-input[id="COMP6064"]', produtos[idx]['UNIDADE.1'])
        print("Incluído.")

        valor_atual = acessar_valor(wa_panel).strip()  # Remove espaços extras
        print(f"Valor atual do campo: {valor_atual}")
        
        valor_desejado = str(produtos[idx]['UNIDADE.1']).strip()

        confirma_valor(driver, valor_atual, valor_desejado, wa_panel, 'wa-panel[id="COMP6029"] > wa-text-input[id="COMP6064"]')

        time.sleep(3)

        print("\nSalvando produto...")
        wait_for_element(driver, By.CSS_SELECTOR, 'wa-panel[id="COMP6550"] > wa-button[id="COMP6554"]')
        shadow_button(driver, 'wa-panel[id="COMP6550"] > wa-button[id="COMP6554"]', 'button')
        print("Salvo.")

        print("\nConfirmando.")
        wait_for_element(driver, By.CSS_SELECTOR, 'wa-panel[id="COMP7509"] > wa-button[id="COMP7511"]')
        shadow_button(driver, 'wa-panel[id="COMP7509"] > wa-button[id="COMP7511"]', 'button')
        print("Confirmado.")
        
        it_prod.atualizar_valor("ultimo_idx", idx+1)
        time.sleep(5)

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

            instan_prod = Produto(r"dist\LINHA CONTRATO AUTO.xlsx")

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