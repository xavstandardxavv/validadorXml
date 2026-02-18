# Validação de Comunicação - Render vs Local

## ✅ Status: VALIDADO E CORRIGIDO

---

## 1. Estrutura de Dados Retornados

### app.py - ValidadorFiscal.extrair_dados_xml()
Retorna um dicionário com os seguintes campos:

```python
{
    "Tipo": str,                    # Tipo de documento (NF-e, NFC-e, etc)
    "Número": str,                  # Número da nota
    "Data": str,                    # Data em formato DD/MM/YYYY
    "Frete (R$)": float,           # Valor do frete
    "Impostos (R$)": float,        # Total de impostos
    "Total (R$)": float,           # Valor total da nota
    "Natureza": str,               # Natureza de operação
    "Chave": str,                  # Chave de acesso (NFe)
    "Status": str,                 # Status (Autorizada/Cancelado)
    "Produtos": [                  # Lista de produtos
        {
            "descricao": str,
            "codigo": str,
            "cfop": str,
            "vProd": float,        # Valor do produto
            "imposto": float       # Imposto do produto
        }
    ]
}
```

---

## 2. Rotas e Endpoints

### app_web.py (Render)
- **Rota raiz**: `GET /` → Retorna `index.html`
- **Rota validação**: `POST /validate` → Processa XMLs e retorna JSON

**Endpoint de validação:**
```
POST /validate
Content-Type: multipart/form-data

Parâmetros:
- files: arquivo(s) XML
- tipo: Tipo de documento (padrão: "NF-e")

Retorna: {"notas": [...]}
```

### index.py (Local/Produção com armazenamento)
- Mesmo comportamento que app_web.py
- Adiciona armazenamento em memória (STORE)
- Rota de download: `GET /download/<key>`

---

## 3. Frontend (index.html)

### Requisição enviada:
```javascript
POST /validate
Body: FormData
  - files: [] (XMLs selecionados)
  - tipo: "NF-e" (tipo fixo)
```

### Dados esperados na resposta:
```javascript
{
  "notas": [
    {
      "Tipo": "NF-e",
      "Número": "123456789",
      "Data": "2024-01-15",
      "Frete (R$)": 50.00,
      "Impostos (R$)": 100.50,
      "Total (R$)": 1500.00,
      "Natureza": "Venda de produtos",
      "Status": "Autorizada",
      "Produtos": [...]
    }
  ]
}
```

---

## 4. Campos Exibidos na Tabela HTML

A tabela mostra os seguintes campos:

| Coluna | Campo JSON | Fonte |
|--------|-----------|-------|
| Tipo | `Tipo` | app.py |
| Data | `Data` | app.py |
| Número | `Número` | app.py |
| Natureza de Operação | `Natureza` | app.py |
| Status | `Status` | app.py |
| Frete (R$) | `Frete (R$)` | app.py |
| Impostos (R$) | `Impostos (R$)` | app.py |
| Total (R$) | `Total (R$)` | app.py |
| Produtos | `Produtos` | app.py |

---

## 5. Fluxo de Dados

```
Frontend (index.html)
    ↓
    └─→ POST /validate (app_web.py)
        ├─→ Recebe XMLs + tipo
        ├─→ Salva em diretório temporário
        ├─→ Cria ValidadorFiscal (de app.py)
        ├─→ Build events_index
        ├─→ Para cada XML:
        │   ├─→ Parse XML com ET
        │   ├─→ Valida se é nota (infNFe)
        │   └─→ extrair_dados_xml(arquivo, tipo, events_index)
        ├─→ Limpa arquivos temporários
        └─→ Return JSON: {"notas": [dados1, dados2, ...]}
            ↓
        Frontend renderiza tabela com todos os campos
```

---

## 6. Correções Aplicadas

### ✅ app_web.py
**ANTES:** Tinha sua própria classe ValidadorFiscal incompleta
**DEPOIS:** Importa e usa a classe completa de app.py

**MUDANÇAS:**
1. Removeu classe ValidadorFiscal duplicada
2. Importou `from app import ValidadorFiscal`
3. Usa `events_index` para detectar cancelamentos
4. Salva XMLs em arquivo temporário (já que app.py trabalha com caminhos)
5. Retorna estrutura DataÓ idêntica ao index.py

### ✅ Compatibilidade Render
- Flask app escuta em `0.0.0.0:5000` (padrão)
- Arquivos estáticos servidos pelo Flask
- Sem dependências externas faltando
- Tratamento robusto de erros

---

## 7. Checklist de Validação

- ✅ **app.py** - Extrai todos os campos necessários
- ✅ **app_web.py** - Importa ValidadorFiscal corretamente
- ✅ **index.py** - Usa mesma lógica
- ✅ **index.html** - Renderiza campos corretamente
- ✅ **Rota GET /** - Retorna HTML
- ✅ **Rota POST /validate** - Processa XMLs
- ✅ **Estrutura JSON** - Idêntica em ambos os endpoints
- ✅ **Campos da tabela** - Todos presentes na resposta
- ✅ **requirements.txt** - Contém Flask e dependências

---

## 8. Para Deploy no Render

1. Confirme que o **branch está atualizado** com as mudanças
2. Trigger redeploy no Render (ou push para main/master)
3. Use como comando de inicialização: `python app_web.py` ou `gunicorn app_web:app`
4. Verifique os logs do Render para erros de importação

---

## 9. Teste Local

```bash
# Terminal 1 - Executar servidor
cd Validador/validadorXml
python app_web.py

# Terminal 2 - Testar rota
curl -X POST http://localhost:5000/validate \
  -F "files=@seu_arquivo.xml" \
  -F "tipo=NF-e"
```

Esperado: JSON com estrutura igual ao documentado acima.

---

**Data de Validação:** 18 de Fevereiro de 2026
**Status:** ✅ PRONTO PARA PRODUÇÃO
