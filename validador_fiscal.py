import xml.etree.ElementTree as ET
import pandas as pd
from fpdf import FPDF
from datetime import datetime

class ValidadorFiscal:
    def __init__(self):
        self.dados_extracao = []

    def limpar_tag(self, tag):
        return tag.split('}', 1)[1] if '}' in tag else tag

    def buscar_valor(self, root, tags):

        tags_lower = [t.lower() for t in tags]
        for elemento in root.iter():
            if self.limpar_tag(elemento.tag).lower() in tags_lower:
                return elemento.text or "0.00"
        return "0.00"

    def processar_xml(self, caminho, tipo):

        try:
            dados = self.extrair_dados_xml(caminho, tipo)
            self.dados_extracao = [dados]
            return self.formatar_relatorio_texto(dados)
        except Exception as e:
            return f"Erro: {e}"

    def extrair_dados_xml(self, caminho, tipo, events_index=None):
        tree = ET.parse(caminho)
        root = tree.getroot()

        numero = self.buscar_valor(root, ['nNF', 'Numero', 'numNota', 'nCT', 'nMDF'])
        data = self.buscar_valor(root, ['dhEmi', 'DataEmissao', 'dEmi', 'dhEmiS'])
        v_nota = self.buscar_valor(root, ['vNF', 'vServ', 'vLiquido', 'vProd', 'vTPrest'])
        v_frete = self.buscar_valor(root, ['vFrete', 'vFreteT'])
        v_imp = self.buscar_valor(root, ['vTotTrib', 'vICMS', 'vISS', 'vTot'])
        natureza = self.buscar_valor(root, ['natOp', 'natureza'])

        chave = None
        for elemento in root.iter():
            if self.limpar_tag(elemento.tag).lower() == 'infnfe':
                chave_attr = elemento.attrib.get('Id') or elemento.attrib.get('ID')
                if chave_attr:
                    chave = chave_attr.replace('NFe', '').strip()
                    break

        if not chave:
            ch = self.buscar_valor(root, ['chNFe', 'chave'])
            if ch and ch != '0.00':
                chave = ch.strip()

        status = 'Autorizada'
        if events_index and chave:
            evs = events_index.get(chave, [])
            if evs:
                for ev in evs:
                    tp = ev.get('tpEvento') if isinstance(ev, dict) else None
                    xev = ev.get('xEvento') if isinstance(ev, dict) else None
                    root_ev = ev.get('root') if isinstance(ev, dict) else ev
                    if tp and str(tp).strip() == '110111':
                        status = 'Cancelado'
                        break
                    txt = ''
                    if xev:
                        txt += str(xev).lower()
                    if root_ev is not None:
                        txt += ''.join([(el.text or '').lower() for el in root_ev.iter()])
                    if 'cancelamento' in txt or 'cancelado' in txt or 'cancel' in txt or '110111' in txt:
                        status = 'Cancelado'
                        break

        def to_float_safe(v):
            try:
                return float(str(v).replace(',', '.'))
            except:
                return 0.0

        produtos = []
        for det in root.iter():
            if self.limpar_tag(det.tag).lower() == 'det':
                prod_el = None
                for child in det:
                    if self.limpar_tag(child.tag).lower() == 'prod':
                        prod_el = child
                        break
                if prod_el is None:
                    continue
                desc = self.buscar_valor(prod_el, ['xProd', 'descr', 'descricao'])
                codigo = self.buscar_valor(prod_el, ['cProd', 'codigo', 'cProdItem'])
                cfop = self.buscar_valor(prod_el, ['CFOP', 'cfop'])
                vprod = self.buscar_valor(prod_el, ['vProd', 'vproduto', 'vProdItem'])
                imposto_tags = ['vICMS', 'vIPI', 'vPIS', 'vCOFINS', 'vII', 'vST']
                imposto_total = 0.0
                for tag in imposto_tags:
                    val = None
                    for el in det.iter():
                        if self.limpar_tag(el.tag).lower() == tag.lower() and el.text:
                            try:
                                imposto_total += float(el.text.replace(',', '.'))
                            except:
                                pass
                produtos.append({
                    'descricao': desc if desc and desc != '0.00' else '',
                    'codigo': codigo if codigo and codigo != '0.00' else '',
                    'cfop': cfop if cfop and cfop != '0.00' else '',
                    'vProd': float(str(vprod).replace(',', '.')) if vprod and vprod != '0.00' else 0.0,
                    'imposto': imposto_total
                })

        dados = {
            "Tipo": tipo,
            "Número": numero,
            "Data": data[:10] if data and data != '0.00' else "N/A",
            "Frete (R$)": to_float_safe(v_frete),
            "Impostos (R$)": to_float_safe(v_imp),
            "Total (R$)": to_float_safe(v_nota),
            "Natureza": natureza,
            "Chave": chave or '',
            "Status": status,
            "Produtos": produtos
        }
        return dados

    def formatar_relatorio_texto(self, d):
        return (f"RELATÓRIO GERADO\n{'='*20}\n"
                f"Tipo: {d['Tipo']}\nNota nº: {d['Número']}\nData: {d['Data']}\n"
                f"Frete: R$ {d['Frete (R$)']:.2f}\nImpostos: R$ {d['Impostos (R$)']:.2f}\n"
                f"Total: R$ {d['Total (R$)']:.2f}\nNatureza: {d.get('Natureza','')}\nStatus: {d.get('Status','')}")

    def build_events_index(self, file_paths):
        index = {}
        for f in file_paths:
            try:
                tree = ET.parse(f)
                root = tree.getroot()
                chave = None
                tpEvento = None
                xEvento = None
                for el in root.iter():
                    tag = self.limpar_tag(el.tag).lower()
                    if tag == 'chnfe' and el.text:
                        chave = el.text.strip()
                    if tag == 'tpevento' and el.text:
                        tpEvento = el.text.strip()
                    if tag == 'xevento' and el.text:
                        xEvento = el.text.strip()
                if not chave:
                    for el in root.iter():
                        if self.limpar_tag(el.tag).lower() == 'chnfe' and el.text:
                            chave = el.text.strip()
                            break
                if chave:
                    index.setdefault(chave, []).append({'tpEvento': tpEvento, 'xEvento': xEvento, 'root': root})
            except Exception:
                continue
        return index

    def exportar_excel(self, caminho=None):
        if not self.dados_extracao:
            return
        show_msg = lambda *a, **k: None
        show_err = lambda *a, **k: None
        if not caminho:
            try:
                import tkinter as _tk
                from tkinter import filedialog as _filedialog, messagebox as _messagebox
                caminho = _filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx")])
                show_msg = _messagebox.showinfo
                show_err = _messagebox.showerror
            except Exception:
                raise RuntimeError("Ambiente sem GUI: forneça o parâmetro 'caminho' para exportar_excel")
        if not caminho:
            return

        rows = []
        notas = self.dados_extracao if isinstance(self.dados_extracao, list) else [self.dados_extracao]
        for nota in notas:
            row_note = {
                'Tipo': nota.get('Tipo',''),
                'Data': nota.get('Data',''),
                'Número': nota.get('Número',''),
                'Natureza de Operação': nota.get('Natureza',''),
                'Status': nota.get('Status',''),
                'Frete': nota.get('Frete (R$)',0.0),
                'Impostos': nota.get('Impostos (R$)',0.0),
                'Total': nota.get('Total (R$)',0.0),
                'Produto': '',
                'CFOP': '',
                'Valor Produto': '',
                'Imposto Produto': ''
            }
            rows.append({'row': row_note, 'level': 0})
            for p in nota.get('Produtos', []):
                row_prod = {
                    'Tipo': '',
                    'Data': '',
                    'Número': '',
                    'Natureza de Operação': '',
                    'Status': '',
                    'Frete': '',
                    'Impostos': '',
                    'Total': '',
                    'Código Produto': p.get('codigo',''),
                    'Produto': p.get('descricao',''),
                    'CFOP': p.get('cfop',''),
                    'Valor Produto': p.get('vProd',0.0),
                    'Imposto Produto': p.get('imposto',0.0)
                }
                rows.append({'row': row_prod, 'level': 1})

        try:
            with pd.ExcelWriter(caminho, engine='xlsxwriter') as writer:
                workbook = writer.book
                worksheet = workbook.add_worksheet('Notas')
                writer.sheets['Notas'] = worksheet

                headers = ['Tipo','Data','Número','Natureza de Operação','Status','Frete','Impostos','Total','Código Produto','Produto','CFOP','Valor Produto','Imposto Produto']
                header_format = workbook.add_format({'bold': True, 'bg_color': '#DCE6F1'})
                for c, h in enumerate(headers):
                    worksheet.write(0, c, h, header_format)

                row_idx = 1
                money_fmt = workbook.add_format({'num_format': '#,##0.00'})
                for item in rows:
                    r = item['row']
                    lvl = item['level']
                    worksheet.write(row_idx, 0, r.get('Tipo',''))
                    worksheet.write(row_idx, 1, r.get('Data',''))
                    worksheet.write(row_idx, 2, r.get('Número',''))
                    worksheet.write(row_idx, 3, r.get('Natureza de Operação',''))
                    worksheet.write(row_idx, 4, r.get('Status',''))
                    
                    if r.get('Frete','') != '':
                        worksheet.write_number(row_idx, 5, float(r.get('Frete',0.0)), money_fmt)
                    else:
                        worksheet.write(row_idx, 5, '')
                    if r.get('Impostos','') != '':
                        worksheet.write_number(row_idx, 6, float(r.get('Impostos',0.0)), money_fmt)
                    else:
                        worksheet.write(row_idx, 6, '')
                    if r.get('Total','') != '':
                        worksheet.write_number(row_idx, 7, float(r.get('Total',0.0)), money_fmt)
                    else:
                        worksheet.write(row_idx, 7, '')

                    worksheet.write(row_idx, 8, r.get('Código Produto',''))
                    worksheet.write(row_idx, 9, r.get('Produto',''))
                    worksheet.write(row_idx, 10, r.get('CFOP',''))
                    if r.get('Valor Produto','') != '':
                        worksheet.write_number(row_idx, 11, float(r.get('Valor Produto',0.0)), money_fmt)
                    else:
                        worksheet.write(row_idx, 11, '')
                    if r.get('Imposto Produto','') != '':
                        worksheet.write_number(row_idx, 12, float(r.get('Imposto Produto',0.0)), money_fmt)
                    else:
                        worksheet.write(row_idx, 12, '')

                    if lvl == 1:
                        worksheet.set_row(row_idx, None, None, {'level': lvl, 'hidden': True})
                    else:
                        worksheet.set_row(row_idx, None, None, {'level': lvl, 'collapsed': True})
                    row_idx += 1

                total_autorizadas = 0.0
                for nota in notas:
                    try:
                        if nota.get('Status') != 'Cancelado':
                            total_autorizadas += float(nota.get('Total (R$)', nota.get('Total', 0.0) or 0.0))
                    except:
                        pass
                worksheet.write(row_idx, 6, 'TOTAL AUTORIZADAS', header_format)
                worksheet.write_number(row_idx, 7, total_autorizadas, money_fmt)

                worksheet.set_column(0, 0, 12)
                worksheet.set_column(1, 1, 12)
                worksheet.set_column(2, 2, 12)
                worksheet.set_column(3, 3, 30)
                worksheet.set_column(4, 4, 12)
                worksheet.set_column(5, 7, 12)
                worksheet.set_column(8, 8, 14)
                worksheet.set_column(9, 9, 40)
                worksheet.set_column(10, 10, 10)
                worksheet.set_column(11, 12, 14)

            show_msg("Sucesso", "Excel gerado com sucesso")
        except Exception as e:
            show_err('Erro', f'Falha ao gerar Excel: {e}')

    def exportar_pdf(self, caminho=None):

        if not self.dados_extracao:
            return
        show_msg = lambda *a, **k: None
        show_err = lambda *a, **k: None
        if not caminho:
            try:
                import tkinter as _tk
                from tkinter import filedialog as _filedialog, messagebox as _messagebox
                caminho = _filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF", "*.pdf")])
                show_msg = _messagebox.showinfo
                show_err = _messagebox.showerror
            except Exception:
                raise RuntimeError("Ambiente sem GUI: forneça o parâmetro 'caminho' para exportar_pdf")
        if not caminho:
            return
        try:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(200, 10, txt="Relatório de Validação Fiscal", ln=True, align='C')
            pdf.set_font("Arial", size=12)
            pdf.ln(10)
            if isinstance(self.dados_extracao, list):
                for d in self.dados_extracao:
                    pdf.set_font("Arial", 'B', 12)
                    pdf.cell(0, 8, txt=f"Nota: {d.get('Número','')} - Chave: {d.get('Chave','')}", ln=True)
                    pdf.set_font("Arial", size=11)
                    pdf.cell(0, 6, txt=f"Tipo: {d.get('Tipo','')}  Data: {d.get('Data','')}", ln=True)
                    pdf.cell(0, 6, txt=f"Status: {d.get('Status','')}  Natureza: {d.get('Natureza','')}", ln=True)
                    pdf.cell(0, 6, txt=f"Total: R$ {d.get('Total (R$)',0):.2f}  Frete: R$ {d.get('Frete (R$)',0):.2f}", ln=True)
                    pdf.ln(4)
            else:
                for chave, valor in self.dados_extracao.items():
                    pdf.cell(200, 10, txt=f"{chave}: {valor}", ln=True)
            pdf.output(caminho)
            show_msg("Sucesso", "PDF gerado com sucesso!")
        except Exception as e:
            show_err('Erro', f'Falha ao gerar PDF: {e}')
