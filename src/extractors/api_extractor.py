import requests
import time
import logging
from tqdm.auto import tqdm
from typing import List, Dict, Any, Tuple

# Isso eu aprendi nesse projeto
log = logging.getLogger(__name__) # Cria um logger para este módulo
if not log.handlers:              # Isso evita configurar o logger + de uma vez
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

class ExtratorAPI:
    """
    Classe para extrair dados da API ObrasGov
    """
    def __init__(self,
                 url_base: str,
                 params: Dict[str, Any],
                 max_tentativas: int = 20, 
                 pausa_requisicoes_s: int = 30, 
                 backoff_base_s: int = 30):
        """
        Construtor da classe ExtratorAPI

        Args:
            url_base (str): A URL principal da API.
            params (Dict): Dicionário com os parâmetros da requisição.
                               Deve incluir a página inicial, ex: {'pagina': 0}.
            max_tentativas (int): Número máximo de retentativas em caso de falha.
            pausa_requisicoes_s (int): Pausa em segundos após cada requisição bem-sucedida.
            backoff_base_s (int): Fator base em segundos para a espera após um erro (ex: 60s).
        """
        self.url_base = url_base
        self.params = params.copy()
        self.max_tentativas = max_tentativas
        self.pausa_requisicoes_s = pausa_requisicoes_s
        self.backoff_base_s = backoff_base_s
        
        # Nomes de chaves específicas da API do ObrasGov
        self.param_pagina = 'pagina'
        self.param_conteudo = 'content'

        # Validação inicial
        if self.param_pagina not in self.params:
            raise ValueError(f"O dicionário de parâmetros deve conter a chave '{self.param_pagina}'")

    def executar_extracao(self) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Orquestra o processo completo de extração de dados da API.

        Returns:
            Uma tupla contendo:
            - A lista de todos os registros de dados coletados.
            - A lista de todos os metadados de cada página.
        """
        log.info(f"Iniciando extração da API em '{self.url_base}'")
        
        data_totais = []
        metadata_totais = []
        count_attempts = 0

        with tqdm(desc="Páginas extraídas", unit=" pág") as pbar:
            while True:
                try:
                    response = requests.get(self.url_base, params=self.params)
                    log.info(f"Requisitando URL: {response.url}")
                    response.raise_for_status()  # Levanta erro para status 4xx/5xx

                    # Requisição deu certo -> reseta o contador de tentativas
                    count_attempts = 0
                    
                    data_pagina = response.json()
                    
                    # Coleta de metadados
                    metadata_pagina = data_pagina.copy()
                    metadata_pagina.pop(self.param_conteudo, None)
                    metadata_totais.append(metadata_pagina)

                    # Coleta dos dados principais
                    conteudo = data_pagina.get(self.param_conteudo, [])
                    if not conteudo:
                        log.info(f"Nenhum dado encontrado na página {self.params[self.param_pagina]}. Extração concluída.")
                        break
                    
                    data_totais.extend(conteudo) # Adiciona os dados da página atual ao total
                    pbar.update(1) 
                    pbar.set_postfix(registros_coletados=len(data_totais))

                    # Prepara para a próxima página
                    self.params[self.param_pagina] += 1
                    time.sleep(self.pausa_requisicoes_s)

                except requests.exceptions.HTTPError as http_err:
                    status_code = http_err.response.status_code
                    count_attempts += 1

                    if count_attempts > self.max_tentativas:
                        log.error("Número máximo de tentativas excedido. Abortando.")
                        break

                    if status_code == 429 or status_code >= 500:
                        # Lógica de backoff linear, como no script funcional
                        tempo_espera = self.backoff_base_s * count_attempts
                        log.warning(f"Erro {status_code}. Tentativa {count_attempts}/{self.max_tentativas}. Aguardando {tempo_espera}s...")
                        time.sleep(tempo_espera)
                        continue # Tenta a mesma página novamente
                    else:
                        log.error(f"Erro HTTP {status_code} não recuperável: {http_err}. Abortando.")
                        break

                except requests.exceptions.RequestException as req_err:
                    log.error(f"Erro crítico de conexão: {req_err}. Abortando.")
                    break
        
        log.info("--- Resumo da Extração ---")
        log.info(f"Total de registros coletados: {len(data_totais)}")
        log.info(f"Total de páginas de metadados salvas: {len(metadata_totais)}")
        
        return data_totais, metadata_totais