import unicodedata
import re
from typing import Iterable

import pandas as pd

def normalize_cols_names(df, inplace: bool = False):
    """Padroniza nomes de colunas para snake_case removendo acentos e caracteres especiais.

    Parameters:
    - df: pandas.DataFrame
    - inplace: se True, renomeia no local e retorna o mesmo df; se False retorna uma cópia renomeada
    """
    def _clean(name: str):
        if not isinstance(name, str):
            return name
        s = unicodedata.normalize('NFKD', name)
        s = ''.join(ch for ch in s if not unicodedata.combining(ch))
        s = s.replace('º', '').replace('ª', '')
        s = re.sub(r"\s+", '_', s)
        s = re.sub(r'[^0-9A-Za-z_]', '_', s)
        s = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', s)
        s = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s)
        s = s.lower()
        s = re.sub(r'_+', '_', s).strip('_')
        return s

    mapping = {c: _clean(c) for c in df.columns}
    if inplace:
        df.rename(columns=mapping, inplace=True)
        return df
    return df.rename(columns=mapping)


def normalize_cols_multivalorada(df: pd.DataFrame, coluna_id: str, coluna_aninhada: str) -> pd.DataFrame:
    """Explode and normalize a nested-list column into a flat DataFrame.

    Parameters:
    - df : pandas.DataFrame
    - coluna_id : str
    coluna_aninhada : str

    Returns:
    - pandas.DataFrame
    """
    # Filtra linhas onde a coluna aninhada não está vazia
    df_filtrado = df[[coluna_id, coluna_aninhada]].dropna(subset=[coluna_aninhada]).explode(coluna_aninhada)

    # Se após o explode a coluna estiver vazia, retorna um DataFrame vazio
    if df_filtrado.empty:
        return pd.DataFrame()

    # Normaliza o dicionário em colunas
    df_normalizado = pd.json_normalize(df_filtrado[coluna_aninhada])

    # Adiciona o ID do projeto para o join
    df_final = df_normalizado.set_index(df_filtrado.index).join(df_filtrado[coluna_id])

    # Reorganiza as colunas para ter o ID primeiro
    return df_final[[coluna_id] + [col for col in df_final.columns if col != coluna_id]]
