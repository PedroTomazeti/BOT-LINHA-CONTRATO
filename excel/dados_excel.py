import pandas as pd
from web.web_app import iniciar_driver

class DadosExcel:
    def __init__(self, caminho_arquivo):
        # Ler o arquivo Excel
        self.df = pd.read_excel(caminho_arquivo, engine="openpyxl")

        # Definir as colunas desejadas
        self.colunas_desejadas = ['GRUPO', 'DESCRICAO', 'TIPO', 'UN', 'ARMAZEM', 'NCM', 
                                  'PRECO VENDA', 'COD FOR', 'COD PRO CLI', 'NI']
        
        # Filtrar as colunas existentes
        self.df = self.df[[col for col in self.colunas_desejadas if col in self.df.columns]]

    # Método __iter__ para permitir iteração sobre os dados
    def __iter__(self):
        # Iterar sobre as linhas do DataFrame e retornar um dicionário para cada linha
        for _, row in self.df.iterrows():
            # Formatar o preço de venda
            preco_venda = f"{row['PRECO VENDA']:.2f}".replace('.', ',')  # Formata o preço com vírgula
            produto = {
                'GRUPO': row['GRUPO'],
                'DESCRICAO': row['DESCRICAO'],
                'TIPO': row['TIPO'],
                'UNIDADE': row['UN'],
                'ARMAZEM': row['ARMAZEM'],
                'NCM': str(row['NCM']) * 8,
                'PRECO VENDA': preco_venda,  # Preço já formatado
                'COD FOR': row['COD FOR'],
                'COD PRO CLI': row['COD PRO CLI'],
                'UNIDADE.1': row['NI']
            }
            yield produto  # Retorna o dicionário com os dados da

# Exemplo de uso
caminho_arquivo = r"C:\Users\Pedro\Documents\BOT-PRODUTO\dist\ALUNORTE AT.xlsx"  # Substitua pelo caminho correto
dados = DadosExcel(caminho_arquivo)

iniciar_driver(dados)