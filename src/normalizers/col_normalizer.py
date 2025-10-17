import unicodedata
import re

def normalize_columns(df, inplace: bool = False):
    """Padroniza nomes de colunas para snake_case removendo acentos e caracteres especiais.

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
