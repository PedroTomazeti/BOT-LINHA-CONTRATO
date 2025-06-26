import pandas as pd
from web.web_app import iniciar_driver

class DadosExcel:
    def __init__(self, caminho_arquivo):
        # Ler o arquivo Excel
        self.df = pd.read_excel(caminho_arquivo, engine="openpyxl")

        # Definir as colunas desejadas
        self.colunas_desejadas = ['Grupo', 'Codigo', 'Descricao', 'Preco Venda', 'Tipo', 'Unidade', 
                                  'Armazem Pad.', 'Pos.IPI/NCM', 'Cod. For', 'Cod.Prod.Cli']
        
        # Filtrar as colunas existentes
        self.df = self.df[[col for col in self.colunas_desejadas if col in self.df.columns]]

        # Filtrar apenas onde Unidade == 'UN'
        self.df = self.df[self.df['Unidade'] == 'UN']

        # Mostrar quantidade
        print(f"Quantidade de produtos com Unidade 'UN': {len(self.df)}")

    # Método __iter__ para permitir iteração sobre os dados
    def __iter__(self):
        for _, row in self.df.iterrows():
            preco_venda = f"{row['Preco Venda']:.2f}".replace('.', ',')  # Formatar preço com vírgula
            codigo_formatado = "{:04.4f}".format(row["Codigo"])
            produto = {
                'Grupo': row['Grupo'],
                'Codigo': codigo_formatado,
                'Descricao': row['Descricao'],
                'Unidade': row['Unidade'],
                'Armazem Pad.': row['Armazem Pad.'],
                'Pos.IPI/NCM': row['Pos.IPI/NCM'],
                'Preco Venda': preco_venda,
                'Cod. For': row['Cod. For'],
                'Cod.Prod.Cli': row['Cod.Prod.Cli'],
            }
            yield produto

# Exemplo de uso
caminho_arquivo = r"C:\Users\Pedro\Documents\BOT-PRODUTO\dist\mata010.xlsx"  # Substitua pelo caminho correto
dados = DadosExcel(caminho_arquivo)

iniciar_driver(dados)
