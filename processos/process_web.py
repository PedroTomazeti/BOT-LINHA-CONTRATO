from time import sleep
import re
import pandas as pd
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from path.paths import PATH_SLZ, PATH_PRP, PATH_SJC

# Variável global para rastrear o número de tentativas
tentativas = 0
limite_tentativas = 5
unidades = ['0102', '0103', '0104']

def normal_input(driver, seletor_container, seletor_field, text, tipo ):
    container = wait_for_element(driver, By.CSS_SELECTOR, seletor_container)
        
    field = wait_for_click(container, By.CSS_SELECTOR, seletor_field)

    ActionChains(driver).move_to_element(field).perform()
    
    field.clear()

    field.send_keys(text)
    print(f"{tipo} inserido(a) com sucesso.")

def expand_shadow_element(driver, element):
    """Expande o Shadow DOM de um elemento"""
    return driver.execute_script("return arguments[0].shadowRoot", element)

def shadow_button(driver, shadow_host_selector, botao_selector):
    """
    Expande um Shadow DOM e clica em um botão específico dentro dele. (Obrigado Schenaid).
    """
    print(f"Aguardando Shadow Host: {shadow_host_selector}")
    shadow_host = wait_for_element(driver, By.CSS_SELECTOR, shadow_host_selector)
    shadow_root = expand_shadow_element(driver, shadow_host)

    print(f"Localizando botão: {botao_selector}")
    botao = wait_for_element(shadow_root, By.CSS_SELECTOR, botao_selector)

    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", botao)
    print("Clicando no botão...")
    driver.execute_script("arguments[0].click();", botao)

    sleep(1.5)

def button(driver, shadow_button):
    """Clique em um botão dentro do Shadow DOM do elemento."""
    WebDriverWait(shadow_button, 20).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, 'button'))
    )
    button = shadow_button.find_element(By.CSS_SELECTOR, 'button')
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
    driver.execute_script("arguments[0].click();", button)
    print("Botão encontrado e clicado com sucesso.")

def shadow_input(driver, element, text):
    """Acessa um input dentro do Shadow DOM de um elemento."""
    input = wait_for_element(driver, By.CSS_SELECTOR, element)
    shadow = expand_shadow_element(driver, input)
    print("Shadow DOM expandido.")
    inserir = wait_for_click(shadow, By.CSS_SELECTOR, 'input')
    sleep(1)

    driver.execute_script("arguments[0].focus();", inserir)
    inserir.clear()
    sleep(1)
    inserir.send_keys(Keys.CONTROL, 'a')
    sleep(0.3)
    inserir.send_keys(Keys.BACKSPACE)
    ActionChains(driver).move_to_element(inserir).perform()
    input.send_keys(text)

    sleep(0.3)
    
    print("\nValor inserido.")

    return inserir

def wait_for_element(driver, by, value, timeout=60):
    """Função para esperar um elemento aparecer no DOM"""
    return WebDriverWait(driver, timeout).until(EC.presence_of_element_located((by, value)))

def wait_for_click(host, by, value, timeout=60):
    return WebDriverWait(host, timeout).until(EC.element_to_be_clickable((by, value)))

def click_element(driver, element, timeout=60):
    """Função para esperar e clicar em um elemento"""
    WebDriverWait(driver, timeout).until(EC.element_to_be_clickable(element)).click()

def confirmar_element(driver, by, value, timeout=20):
    """
    Função pra confirmar que o elemento vai aparecer depois de apertar o botão.
    """
    for i in range(3):
        print(f"Tentativa({i+1}) para encontrar o elemento")
        elemento_confirmado = WebDriverWait(driver, timeout).until(EC.presence_of_element_located((by, value)))
        if elemento_confirmado:
            print("Elemento encontrado.")
            return True

def confirmar_valor(first_info, valor_desejado):
    """Função para comparar valores."""
    if str(first_info) != str(valor_desejado):
        print(valor_desejado)
        print("Valor não inserido corretamente. Refazendo processo.")
        sleep(3)
        return False
    else:
        print("Valor confirmado. Continuando processo.")
        return True

def confirmando_wa_tgrid(driver, id, posicao, valor_desejado, funcao, tipo, *args, **kwargs):
    """Função para confirmar valores de CNPJ, Forma de Pagamento e Natureza"""
    global tentativas
    tentativas += 1

    # Verificar se o número de tentativas excedeu o limite
    if tentativas > limite_tentativas:
        print("Número máximo de tentativas excedido. Encerrando o processo.")
        driver.quit()

    # Localize o elemento principal (wa-tgrid com id específico)
    grid_element = driver.find_element(By.CSS_SELECTOR, f'wa-tgrid[id="{id}"]')

    # Acesse o shadow root
    shadow_root = driver.execute_script("return arguments[0].shadowRoot", grid_element)

    # Localize o elemento na posição especificada
    elements = shadow_root.find_elements(By.CSS_SELECTOR, '*')
    target_element = elements[posicao]

    if posicao in [41, 29, 15, 16]:
        if target_element:
            if tipo == "CNPJ":
                cnpj = valor_desejado.getCNPJ()
                cnpj_text = target_element.text.strip()
                cnpj_numbers = ''.join(filter(str.isdigit, cnpj_text))
                print("CNPJ:", cnpj_numbers)
                if cnpj_numbers != cnpj:
                    print(cnpj)
                    print("Valor incorreto. Tentando novamente...")
                    sleep(5)
                    funcao(driver, valor_desejado, *args, **kwargs)
                else:
                    print("Valor confirmado. Seguindo com a lógica...")
                    tentativas = 0  # Resetar tentativas ao sucesso
            else:
                all_text = target_element.text.strip().splitlines()
                first_info = all_text[0] if all_text else "Não encontrado"
                print("Primeira Informação:", first_info)
                if tipo == "NATUREZA":
                    natureza = valor_desejado.getNAT()
                    confirma = confirmar_valor(first_info, natureza)
                    if confirma:
                        print("Valor confirmado. Continuando processo.")
                        tentativas = 0  # Resetar tentativas ao sucesso
                    else:
                        print(natureza)
                        print("Valor não inserido corretamente. Refazendo processo.")
                        sleep(3)
                        funcao(driver, valor_desejado, *args, **kwargs)
                elif tipo == "PAGTO":
                    pagto = valor_desejado.getPAGTO()
                    confirma = confirmar_valor(first_info, pagto)
                    if confirma:
                        print("Valor confirmado. Continuando processo.")
                        tentativas = 0  # Resetar tentativas ao sucesso
                    else:
                        print(valor_desejado)
                        print("Valor não inserido corretamente. Refazendo processo.")
                        sleep(3)
                        funcao(driver, valor_desejado, *args, **kwargs)
                else:
                    unidade = unidades[valor_desejado-1]
                    confirma = confirmar_valor(first_info, unidade)
                    if confirma:
                        print("Valor confirmado. Continuando processo.")
                        tentativas = 0  # Resetar tentativas ao sucesso
                    else:
                        sleep(3)
                        funcao(driver, valor_desejado, *args, **kwargs)
        else:
            print(f"Elemento na posição {posicao} não encontrado.")

def confirmando_wa_tmsselbr(driver, id, posicao, valor_desejado, funcao, os):
    """Função para confirmar o valor da OS."""
    global tentativas
    tentativas += 1

    # Verificar se o número de tentativas excedeu o limite
    if tentativas > limite_tentativas:
        print("Número máximo de tentativas excedido. Encerrando o processo.")
        driver.quit()

    # Localize o elemento principal (wa-tgrid com id específico)
    grid_element = driver.find_element(By.CSS_SELECTOR, f'wa-tmsselbr[id="{id}"]')

    # Acesse o shadow root
    shadow_root = driver.execute_script("return arguments[0].shadowRoot", grid_element)

    # Localize o elemento na posição especificada
    elements = shadow_root.find_elements(By.CSS_SELECTOR, '*')
    try:
        target_element = elements[posicao]   

        if target_element:
            all_text = target_element.text.strip().splitlines()
            first_info = all_text[0] if all_text else "Não encontrado"
            print("Primeira Informação:", first_info)
            osKairos = os
            if str(first_info) != str(osKairos):
                print(osKairos)
                print("Valor não inserido corretamente. Refazendo processo.")
                sleep(5)
                funcao(driver, valor_desejado)
            else:
                print("Valor confirmado. Continuando processo.")
                tentativas = 0  # Resetar tentativas ao sucesso
        else:
            print(f"Elemento na posição {posicao} não encontrado.")
    
    except IndexError:
        print("Erro: Índice fora do intervalo da lista!")
        print("Valor não inserido corretamente. Refazendo processo.")
        sleep(5)
        funcao(driver, valor_desejado)

def selecionar_elemento(driver, shadow_root, element):
    """Selecionando elemento para construir o corpo da nota."""
    try:
        # Selecionar o elemento-alvo pelo seletor específico
        target_element = shadow_root.find_element(By.CSS_SELECTOR, element)
        if target_element:
            print(f"Elemento localizado: {element}")
            sleep(1)
            # Garantir que o elemento está visível no scroll horizontal
            container = shadow_root.find_element(By.CSS_SELECTOR, 'div.horizontal-scroll')
            driver.execute_script("""
                arguments[0].scrollLeft = arguments[1].getBoundingClientRect().left - arguments[0].getBoundingClientRect().left + arguments[0].scrollLeft;
            """, container, target_element)
            sleep(0.5)  # Pequena pausa para garantir que o scroll foi executado

            # Garantir visibilidade e foco
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", target_element)
            sleep(1)

            # Simular cliques no elemento
            target_element.click()
            sleep(2)

            # Simular a tecla "Enter" com JavaScript
            driver.execute_script("""
                var event = new KeyboardEvent('keydown', {
                    bubbles: true,
                    cancelable: true,
                    key: 'Enter',
                    code: 'Enter',
                    keyCode: 13
                });
                arguments[0].dispatchEvent(event);
            """, target_element)
            sleep(2)

            print("Interação com o elemento concluída com sucesso.")
        else:
            print(f"Elemento não encontrado: {element}")
    except Exception as e:
        print(f"Erro ao interagir com o elemento: {e}")

def acessa_container(driver, element, selector, funcao_seguinte, *args, **kwargs):
    try:
        # Esperar até que o elemento wa-dialog seja carregado
        dialog_element = wait_for_element(driver, By.CSS_SELECTOR, element)

        # Obter o shadowRoot do elemento
        shadow_root = expand_shadow_element(driver, dialog_element)

        if shadow_root:
            selecionar_elemento(driver, shadow_root, selector)
            print("Seleção concluída.")
            funcao_seguinte(driver, *args, **kwargs)
        else:
            print('ShadowRoot não encontrado no elemento.')
    except Exception as e:
        print(f'Ocorreu um erro: {e}')

def compara_data(data_x, data_y):
    """Comparar datas para dar continuidade na emissão das notas"""
    if data_y == data_x:
        print("Datas de emissão iguais, manter.")
        return True
    elif data_y != data_x:
        print("Mudança na data da nota detectada.")
        return False
    
def confirmando_wa_tcbrowse(driver, id, posicao, valor_desejado):
    global tentativas
    tentativas += 1

    # Verificar se o número de tentativas excedeu o limite
    if tentativas > limite_tentativas:
        print("Número máximo de tentativas excedido. Encerrando o processo.")
        driver.quit()

    # Localize o elemento principal (wa-tgrid com id específico)
    grid_element = driver.find_element(By.CSS_SELECTOR, f'wa-tcbrowse[id="{id}"]')

    # Acesse o shadow root
    shadow_root = driver.execute_script("return arguments[0].shadowRoot", grid_element)

    # Localize o elemento na posição especificada
    elements = shadow_root.find_elements(By.CSS_SELECTOR, '*')
    target_element = elements[posicao]   

    if target_element:
        all_text = target_element.text.strip().splitlines()
        first_info = all_text[0] if all_text else "Não encontrado"
        print("Primeira Informação:", first_info)
        if str(first_info) != str(valor_desejado):
            print(valor_desejado)
            print("Valor não inserido corretamente. Refazendo processo.")
            sleep(5)
            return False
        else:
            print("Valor confirmado. Continuando processo.")
            tentativas = 0  # Resetar tentativas ao sucesso
            return True
    else:
        print(f"Elemento na posição {posicao} não encontrado.")
        return False

def clicar_elemento_shadow_dom(driver, dialog_id, browse_id, target_selector, num_nota):
    try:
        # Localizar o elemento wa-dialog no DOM principal
        dialog_element = WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, f'wa-dialog[id="{dialog_id}"] > wa-tcbrowse[id="{browse_id}"]'))
        )

        print("Elemento wa-dialog encontrado.")

        # Obter o ShadowRoot do elemento
        shadow_root = driver.execute_script("return arguments[0].shadowRoot", dialog_element)

        if not shadow_root:
            print("ShadowRoot não encontrado no elemento wa-dialog.")
            return

        print("ShadowRoot expandido com sucesso.")

        # Tentar localizar o elemento dentro do ShadowRoot
        target_element = shadow_root.find_element(By.CSS_SELECTOR, target_selector)

        if not target_element:
            print("Elemento dentro do Shadow DOM não encontrado. Verifique o seletor.")
            return

        print("Elemento localizado dentro do Shadow DOM:", target_element)

        # Simular um clique no elemento
        ActionChains(driver).move_to_element(target_element).click().perform()

        print("Clique realizado com sucesso!")

        sleep(2)

        print("\nExpandindo dialog para análise do número da nota.")
        dialog_element = wait_for_element(driver, By.CSS_SELECTOR, f'wa-dialog[id="{dialog_id}"] > wa-tcbrowse[id="{browse_id}"]')
        
        shadow_root = expand_shadow_element(driver, dialog_element)

        wa_dialog = wait_for_element(shadow_root, By.CSS_SELECTOR, target_selector)
        sleep(2)
        valor_atual = wa_dialog.text.strip()
        print(f"Valor atual do campo: {valor_atual}")
        num_nota = num_nota.strip()  # Garante que também esteja sem espaços extras

        if valor_atual == num_nota:
            print("O valor já está correto, nenhuma alteração necessária.")
            sleep(2)
        else:
            print("\nValores diferentes.")
            # Simular a tecla "Enter" com JavaScript
            driver.execute_script("""
                var event = new KeyboardEvent('keydown', {
                    bubbles: true,
                    cancelable: true,
                    key: 'Enter',
                    code: 'Enter',
                    keyCode: 13
                });
                arguments[0].dispatchEvent(event);
            """, target_element)
            sleep(2)

            print("Interação com o elemento concluída com sucesso.")
            if tentar_alterar_valor(driver, wa_dialog, num_nota, 'wa-dialog[id="COMP7500"] > wa-text-input[id="COMP7501"]'):
                print("Valor alterado com sucesso.")
                sleep(2)
            else:
                print("Falha ao alterar valor")

    except Exception as e:
        print(f"Erro ao interagir com o Shadow DOM: {e}")

def verificar_situacao(driver):
    """
    Verifica a situação de um pedido de venda com base na imagem exibida em uma interface web.

    :param driver: Instância do WebDriver do Selenium.
    :return: None
    """
    try:
        print("Aguardando tela...")
        wa_dialog = wait_for_element(driver, By.CSS_SELECTOR, 'wa-dialog[id="COMP4500"] > wa-tgrid[id="COMP4513"]')
        
        # Acessa o Shadow Root do wa-tgrid
        shadow_root_tgrid = expand_shadow_element(driver, wa_dialog)
        
        # Seleciona o elemento desejado dentro do Shadow DOM
        image_cell = wait_for_element(shadow_root_tgrid, By.CSS_SELECTOR, 'div.horizontal-scroll > table > tbody > tr#\\30 > td#\\30 > div.image-cell')
        print(f"Image cell: {image_cell}")
        
        # Obtém o atributo style
        estilo_inline = image_cell.get_attribute("style")
        print(f"Estilo inline: {estilo_inline}")

        # Extraindo a parte fixa da URL usando regex
        match = re.search(r'background-image:\s*url\("[^"]+/cache/czls4f_prod/([^"]+)"\)', estilo_inline)
        print(f"Match: {match}")

        if match:
            image_url = match.group(1)  # Obtém apenas o nome do arquivo
            status = "Desconhecido"

            # Verifica qual imagem está sendo usada
            if "br_vermelho_mdi" in image_url:
                status = "Encerrado"
            elif "br_verde_mdi" in image_url:
                status = "Em Aberto"
            elif "br_amarelo_mdi" in image_url:
                status = "Liberado"

            print("Status do Pedido de Venda:", status)

            return status
        else:
            print("Não foi possível extrair a imagem.")
    
    except NoSuchElementException as e:
        print(f"Elemento não encontrado: {e}")
    except TimeoutException as e:
        print(f"Tempo de espera excedido: {e}")
    except Exception as e:
        print(f"Erro inesperado: {e}")

def clicar_repetidamente(driver, id_botao, id_objetivo):
    """
    Clica no botão até que o elemento esperado apareça, com um limite de tentativas.
    """
    max_tentativas = 3
    tentativas = 0

    while tentativas < max_tentativas:
        print(f"Tentativa {tentativas + 1} de {max_tentativas}: Clicando no botão...")

        botao = wait_for_element(driver, By.CSS_SELECTOR, id_botao)
        shadow_botao = expand_shadow_element(driver, botao)
        button(driver, shadow_botao)  # Função que realmente clica no botão
        
        sleep(3)
        tentativas += 1
    try:
        # Espera pelo elemento esperado para confirmar que avançou
        botao_objetivo = wait_for_element(driver, By.CSS_SELECTOR, id_objetivo)
        shadow_objetivo = expand_shadow_element(driver, botao_objetivo)
        button(driver, shadow_objetivo)  # Função que realmente clica no botão
        print("Elemento esperado encontrado! Saindo do loop.")
        return True
    except TimeoutException:
        print("Número máximo de tentativas atingido, não foi possível avançar.")
        return False
    
def definir_nfe(unidade, ano, mes):
    """Definição do caminho para a pasta a ser analisada e alterada."""
    match unidade:
        case 1:
            caminho_pdf = f"{PATH_SLZ}/Notas {ano}/{mes}/02 - Serviços"
        case 2:
            caminho_pdf = f"{PATH_PRP}/Notas {ano}/{mes}/02 - Serviços"
        case 3:
            caminho_pdf = f"{PATH_SJC}/Notas {ano}/{mes}/02 - Serviços"
    
    return caminho_pdf

def usar_gatilho(driver, codigo, element, func, *args):
    campo_codigo = wait_for_element(driver, By.CSS_SELECTOR, element)
    shadow_input(driver, element, codigo)

    valor_atual = acessar_valor(campo_codigo)

    print(f"Valor atual do campo: {valor_atual}")

    if valor_atual != codigo:
        if tentar_alterar_valor(driver, campo_codigo, codigo, element):
            print("Valor alterado com sucesso.")
            sleep(3)
            func(driver, *args)
        else:
            print("Falha ao alterar valor")
    else:
        print("O valor já está correto, nenhuma alteração necessária.")

def tentar_alterar_valor(driver, field, valor_desejado, element, max_tentativas=5):
    """
    Tenta alterar o valor do campo e verifica se a alteração foi bem-sucedida.
    Retorna True se a alteração for confirmada, False se falhar após todas as tentativas.
    """
    tentativas = 0

    while tentativas < max_tentativas:
        valor_atual = acessar_valor(field).strip()

        if valor_atual == valor_desejado:
            print(f"Valor alterado com sucesso: {valor_atual}")
            return True  # Sucesso: o valor foi alterado corretamente

        print(f"Tentativa {tentativas+1}/{max_tentativas}: Alterando valor...")

        shadow_input(driver, element, valor_desejado)

        sleep(2)  # Pequena espera para garantir que a alteração seja processada
        tentativas += 1

    print("Erro: Não foi possível confirmar a alteração após múltiplas tentativas.")
    return False  # Falha: o valor não foi alterado corretamente

def acessar_valor(field):
    """
    Obtém o valor atual do campo.
    """
    return field.get_attribute("value")

def gatilho_erro(driver):
    print("\nAcessando wa-dialog de erro no gatilho...")
    shadow_button(driver, 'wa-panel[id="COMP7510"] > wa-button[id="COMP7512"]', 'button')

def confirma_valor(driver, valor_atual, valor_desejado, wa_dialog, element):
    print(f"Valor atual: {valor_atual}")
    print(f"Valor desejado: {valor_desejado}")
    if valor_atual == valor_desejado:
        print("\nO valor já está correto, nenhuma alteração necessária.")
        return True
    else:
        print("\nValores diferentes.")
        if tentar_alterar_valor(driver, wa_dialog, valor_desejado, element):
            print("Valor alterado com sucesso.")
            return True
        else:
            print("Falha ao alterar valor")

def alterar_unidade_para_pc(df, codigos_para_alterar):
    """
    Altera a unidade para 'PC' no DataFrame para os produtos cujo 'Codigo' está na lista ou no código informado.
    Trata o DataFrame removendo espaços e padronizando os códigos.

    Args:
        df (pandas.DataFrame): DataFrame com os dados dos produtos.
        codigos_para_alterar (list or str): Código único ou lista de códigos para alterar.

    Returns:
        pandas.DataFrame: DataFrame alterado.
    """
    if isinstance(codigos_para_alterar, str):
        codigos_para_alterar = [codigos_para_alterar]

    df['Codigo'] = df['Codigo'].astype(str).str.strip()
    codigos_para_alterar = [str(codigo).strip() for codigo in codigos_para_alterar]

    if 'Unidade' in df.columns:
        df['Unidade'] = df['Unidade'].astype(str).str.strip()

    quantidade_alterada = df['Codigo'].isin(codigos_para_alterar).sum()

    df.loc[df['Codigo'].isin(codigos_para_alterar), 'Unidade'] = 'PC'

    print(f"Quantidade de produtos alterados para 'PC': {quantidade_alterada}")

    return df

def formatar_codigo(df):
    """
    Formata o campo 'Codigo' para o padrão 04.4f (ex: 1234.0000).
    """
    try:
        # Tenta converter para float primeiro
        df['Codigo'] = df['Codigo'].astype(float)
    except ValueError:
        print("Erro: Alguns códigos não puderam ser convertidos para número.")

    # Aplica a formatação
    df['Codigo'] = df['Codigo'].apply(lambda x: "{:04.4f}".format(x))

    return df

def processar_arquivo(codigos_para_alterar):
    """
    Carrega o Excel, altera unidades, trata os dados e salva sobrescrevendo o mesmo arquivo.

    Args:
        caminho_arquivo (str): Caminho do arquivo Excel.
        codigos_para_alterar (list or str): Códigos que precisam alterar a unidade.
    """
    caminho_arquivo = r"C:\Users\Pedro\Documents\BOT-PRODUTO\dist\mata010.xlsx"
    print(f"Carregando arquivo: {caminho_arquivo}")
    df = pd.read_excel(caminho_arquivo, engine='openpyxl')

    colunas_desejadas = ['Grupo', 'Codigo', 'Descricao', 'Preco Venda', 'Tipo', 'Unidade', 
                         'Armazem Pad.', 'Pos.IPI/NCM', 'Cod. For', 'Cod.Prod.Cli']
    df = df[[col for col in colunas_desejadas if col in df.columns]]


    # Altera unidades
    df = alterar_unidade_para_pc(df, codigos_para_alterar)

    # Formata os códigos
    df = formatar_codigo(df)

    # Salva no mesmo arquivo
    print(f"Salvando alterações no próprio arquivo: {caminho_arquivo}")
    df.to_excel(caminho_arquivo, index=False, engine='openpyxl')

    print("Arquivo atualizado com sucesso.")

def shadow_input_quant(driver, element, text):
    """Acessa um input dentro do Shadow DOM de um elemento."""
    input = wait_for_element(driver, By.CSS_SELECTOR, element)
    shadow = expand_shadow_element(driver, input)
    print("Shadow DOM expandido.")
    inserir = wait_for_click(shadow, By.CSS_SELECTOR, 'input')
    sleep(1)

    driver.execute_script("arguments[0].focus();", inserir)

    ActionChains(driver).move_to_element(inserir).perform()
    input.send_keys(text)

    sleep(0.5)
    
    print("\nValor inserido.")

    return inserir

def confirma_valor_quant(driver, valor_atual, codigo, wa_dialog, element):
    if valor_atual == codigo:
        print("\nO valor já está correto, nenhuma alteração necessária.")
    else:
        print("\nValores diferentes.")
        if tentar_alterar_valor_quant(driver, wa_dialog, codigo, element):
            print("\nValor alterado com sucesso.")
        else:
            print("\nFalha ao alterar valor")

def tentar_alterar_valor_quant(driver, field, valor_desejado, element, max_tentativas=5):
    """
    Tenta alterar o valor do campo e verifica se a alteração foi bem-sucedida.
    Retorna True se a alteração for confirmada, False se falhar após todas as tentativas.
    """
    tentativas = 0

    while tentativas < max_tentativas:
        valor_atual = str(acessar_valor(field)).strip()

        if valor_atual == valor_desejado:
            print(f"Valor alterado com sucesso: {valor_atual}")
            return True  # Sucesso: o valor foi alterado corretamente

        print(f"Tentativa {tentativas+1}/{max_tentativas}: Alterando valor...")

        shadow_input_quant(driver, element, valor_desejado)

        sleep(2)  # Pequena espera para garantir que a alteração seja processada
        tentativas += 1

    print("Erro: Não foi possível confirmar a alteração após múltiplas tentativas.")
    return False  # Falha: o valor não foi alterado corretamente