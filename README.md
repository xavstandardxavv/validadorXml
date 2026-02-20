# Validador XML

Projeto: Validador XML
Responsável: Gustavo Andrade
Última revisão: 2026-02-20

## Visão Geral

Ferramenta para extrair, validar e gerar relatórios a partir de arquivos XML de notas fiscais eletrônicas (NF-e, NFC-e, NFS-e, CT-e, MDF-e). O módulo principal `validador_fiscal.py` implementa a classe `ValidadorFiscal`, que parseia XMLs, extrai campos relevantes (número, data, totais, produtos, chave de acesso), constrói índice de eventos (ex.: cancelamentos) e prepara dados para exportação em Excel ou PDF.

## Conteúdo do repositório

- `app.py` — Aplicação Flask que expõe endpoints web (UI e API).
- `validador_fiscal.py` — Lógica principal de parsing e extração (classe `ValidadorFiscal`).
- `requirements.txt` — Dependências do projeto.
- `Procfile` / `render.yaml` — Configuração para deploy em Render.
- `templates/`, `static/` — Front-end estático e templates.
- `VALIDADOR_FISCAL_DOC.txt`, `DOCUMENTACAO_PROFISSIONAL.txt` — Documentação técnica detalhada.

## Instalação

1. Crie e ative um ambiente virtual:

```bash
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
# Linux/macOS
source .venv/bin/activate
```

2. Instale dependências:

```bash
pip install -r requirements.txt
```

## Uso rápido (console)

Exemplo mínimo para extrair dados de um XML:

```python
from validador_fiscal import ValidadorFiscal
v = ValidadorFiscal()
resultado = v.extrair_dados_xml('exemplos/nfe.xml', 'NF-e')
print(resultado['Número'], resultado['Total (R$)'])
```

Gerar Excel/PDF sem GUI (em servidor):

```python
# gerar excel
v.dados_extracao = [resultado]
v.exportar_excel(caminho='saida/notas.xlsx')

# gerar pdf
v.exportar_pdf(caminho='saida/notas.pdf')
```

## API pública (resumo)

- `ValidadorFiscal()` — cria instância.
- `extrair_dados_xml(caminho, tipo, events_index=None)` — retorna dict com campos extraídos.
- `build_events_index(file_paths)` — constrói índice de eventos (cancelamentos etc.).
- `exportar_excel(caminho=None)` — exporta para `.xlsx` (se `caminho` for None tenta diálogo GUI).
- `exportar_pdf(caminho=None)` — exporta para `.pdf` (se `caminho` for None tenta diálogo GUI).

## Notas para produção

- O projeto foi ajustado para execução em ambientes headless (Render) — imports de `tkinter` foram removidos do fluxo principal; as funções de exportação aceitam `caminho` para gravação sem GUI.
- Garantir que `requirements.txt` inclua `fpdf2` (já adicionado).
- Use `Procfile` com `web: gunicorn --bind 0.0.0.0:$PORT app:app` para deploy no Render.

## Testes e validação

- Teste manual: utilizar um conjunto de XMLs representativos e validar campos chave (Número, Data, Total, Produtos, Chave).
- Recomenda-se adicionar testes unitários (pytest) para o parser (`extrair_dados_xml`) cobrindo variações de tags e namespaces.

## Segurança

Arquivos XML podem conter dados sensíveis (CNPJ/CPF, valores). Trate-os com cuidado: não exponha storage público, proteja logs e não armazene chaves de acesso sem necessidade.

## Histórico resumido de alterações

- 2026-02-20: Removida execução automática de GUI (tkinter), refatoradas exportações para suportar headless, adicionado `fpdf2` e documentação profissional.

## Contato

Gustavo Andrade — mantenedor do projeto

---

Arquivo de documentação técnica adicional gerado: `DOCUMENTACAO_PROFISSIONAL.txt` e `VALIDADOR_FISCAL_DOC.txt`.
