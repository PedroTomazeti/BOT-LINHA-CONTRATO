import pandas as pd
from utils.Produtos import Produto
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
caminho_arquivo = "dist/LINHA CONTRATO AUTO.xlsx"  # Substitua pelo caminho correto
dados = DadosExcel(caminho_arquivo)

lista_produtos = []

for idx, dado in enumerate(dados):
    lista_produtos.insert(idx, dado)

instan_prod = Produto("dist/register/index_prod.json")

idx_prod = instan_prod.obter_valor("ultimo_idx")

if idx_prod == None:
    print("\nNenhum registro encontrado.")
    instan_prod.atualizar_valor("ultimo_idx", 0)
else:
    print(f"\nRegistro irá retomar na linha {idx_prod + 1} do contrato.")

iniciar_driver(lista_produtos)