# 🚀 GUIA DE DEPLOYMENT - Render

## ⚠️ ANTES DE FAZER QUALQUER COISA

**Faça um commit git com todas as mudanças:**

```bash
cd "C:\Users\gustavo.andrade\Documents\Codes\Validadores-XML\validadorXml"

# Verifique quais arquivos foram modificados
git status

# Adicionar todas as mudanças
git add -A

# Fazer commit
git commit -m "Corrigir extração de dados XML com case-insensitive e logging aprimorado"

# Fazer push para GitHub
git push origin main
```

## 📋 CHECKLIST ANTES DO DEPLOYMENT

- [ ] Arquivo `validador_fiscal.py` tem a função `buscar_valor()` com case-insensitive
- [ ] Arquivo `app.py` tem logging na rota `/validate`
- [ ] Arquivo `Procfile` contém: `web: gunicorn --bind 0.0.0.0:$PORT app:app`
- [ ] Arquivo `requirements.txt` tem apenas 6 pacotes
- [ ] Pasta `static/` existe
- [ ] Arquivo `templates/index.html` existe
- [ ] Todos os arquivos foram commitados no Git

## 🌐 DEPLOYMENT NO RENDER

### Opção 1: Via Dashboard do Render (Recomendado)

1. Abra https://dashboard.render.com
2. Selecione seu serviço (Web Service)
3. Clique em "Manual deploy"
4. Clique em "Deploy latest commit"
5. Aguarde 2-3 minutos para o build completar
6. Verifique o status em "Logs"

### Opção 2: Push automático (Se configurado com GitHub)

Se seu repositório está conectado ao Render:
1. Faça push das mudanças: `git push origin main`
2. Render fará deployment automático
3. Acompanhe em https://dashboard.render.com > Logs

## 📊 ACOMPANHANDO O DEPLOYMENT

1. Acesse https://dashboard.render.com
2. Clique em seu serviço
3. Abra a aba "Logs"
4. Procure por:

   ✅ **SUCESSO:**
   ```
   Building Docker image
   Running build command
   Processando X arquivos
   Running on https://seu-app.onrender.com
   ```

   ❌ **ERRO:**
   ```
   ERROR
   Exception
   ModuleNotFoundError
   ```

## ✅ TESTANDO APÓS DEPLOYMENT

1. Acesse https://seu-app.onrender.com (substitua pelo seu URL)
2. Selecione alguns arquivos XML
3. Clique em "Validar Arquivos"
4. Verifique:

   ✅ Página carrega sem erros  
   ✅ Status muda para "X notas processadas"  
   ✅ Tabela mostra notas com dados reais  
   ✅ Números, datas e totais aparecem  
   ✅ Botão "Produtos (X)" aparece  
   ✅ Ao clicar em produtos, lista aparece  
   ✅ Botão "Baixar Excel" funciona  

## 🐛 TROUBLESHOOTING

### Problema: "Application failed to start"

**Solução:**
1. Verifique `Procfile` - deve ser exatamente: `web: gunicorn --bind 0.0.0.0:$PORT app:app`
2. Verifique `requirements.txt` - todos os pacotes devem estar listados
3. Verifique se `app.py` existe e tem a função `app`

### Problema: "ModuleNotFoundError: No module named 'validador_fiscal'"

**Solução:**
1. Verifique se `validador_fiscal.py` existe no repositório
2. Verifique se foi commitado: `git log --name-status` (deve aparecer validador_fiscal.py)

### Problema: Dados ainda vazios depois do deployment

**Solução:**
1. Verifique os Logs do Render procurando por "Exception"
2. Procure por "Nota sem número" ou "Erro extraindo dados"
3. Se houver error específico, tente novamente com um XML diferente
4. Você pode adicionar mais logging alterando `app.logger.info()` em `app.py`

### Problema: Página fica em "Processando..." eternamente

**Solução:**
1. Pode ser um XML muito grande ou com muitos produtos
2. Tente com um arquivo menor primeiro
3. Se persistir, aumentar timeout em `Procfile`:
   ```
   web: gunicorn --bind 0.0.0.0:$PORT --timeout 120 app:app
   ```

## 📞 SUPORTE

Se o problema persistir:

1. Compartilhe o **arquivo XML de teste** (redacted se for sensível)
2. Compartilhe os **Logs exatos do Render** (copie da aba Logs)
3. Diga exatamente qual é o comportamento esperado vs atual

---

## 📝 RESUMO DAS MUDANÇAS PARA RECORDAR

| Problema | Solução |
|----------|---------|
| Dados vazios | Case-insensitive search em `buscar_valor()` |
| Produtos não aparecem | Melhor lógica em `extrair_dados_xml()` |
| Impossível diagnosticar | Logging aprimorado em `/validate` |
| Build lento no Render | Removidas dependências desktop em `requirements.txt` |
| App não inicia | Procfile com `$PORT` dinâmica |

---

**Status:** ✅ Pronto para produção  
**Última atualização:** 20/02/2026  
**Teste recomendado:** Com 3-5 XMLs diferentes
