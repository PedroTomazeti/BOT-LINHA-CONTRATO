import json, os

class Produto:
    def __init__(self, caminho_arquivo: str):
        self.caminho = caminho_arquivo
        if not os.path.exists(self.caminho):
            # Cria arquivo vazio se não existir
            self.salvar_dados({})

    def salvar_dados(self, dados: dict):
        with open(self.caminho, "w", encoding="utf-8") as f:
            json.dump(dados, f, indent=4)

    def carregar_dados(self) -> dict:
        with open(self.caminho, "r", encoding="utf-8") as f:
            return json.load(f)

    def atualizar_valor(self, chave: str, valor):
        dados = self.carregar_dados()
        dados[chave] = valor
        self.salvar_dados(dados)

    def obter_valor(self, chave: str, valor_padrao=None):
        dados = self.carregar_dados()
        return dados.get(chave, valor_padrao)