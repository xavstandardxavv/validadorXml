import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import xml.etree.ElementTree as ET
import pandas as pd
from fpdf import FPDF
from datetime import datetime

class ValidadorFiscal:
    def __init__(self):
        self.dados_extracao = {} # Armazena o último processamento

    def limpar_tag(self, tag):
        return tag.split('}', 1)[1] if '}' in tag else tag

    def buscar_valor(self, root, tags):
        for elemento in root.iter():
            if self.limpar_tag(elemento.tag) in tags:
                return elemento.text
        return "0.00"

    def processar_xml(self, caminho, tipo):
        try:
            tree = ET.parse(caminho)
            root = tree.getroot()

            # Mapeamento Genérico de Tags
            numero = self.buscar_valor(root, ['nNF', 'Numero', 'numNota', 'nCT', 'nMDF'])
            data = self.buscar_valor(root, ['dhEmi', 'DataEmissao', 'dEmi', 'dhEmiS'])
            v_nota = self.buscar_valor(root, ['vNF', 'vServ', 'vLiquido', 'vProd', 'vTPrest'])
            v_frete = self.buscar_valor(root, ['vFrete', 'vFreteT'])
            v_imp = self.buscar_valor(root, ['vTotTrib', 'vICMS', 'vISS', 'vTot'])

            # Guardar dados para exportação
            self.dados_extracao = {
                "Tipo": tipo,
                "Número": numero,
                "Data": data[:10] if data else "N/A",
                "Frete (R$)": float(v_frete.replace(',', '.')),
                "Impostos (R$)": float(v_imp.replace(',', '.')),
                "Total (R$)": float(v_nota.replace(',', '.'))
            }
            return self.formatar_relatorio_texto()
        except Exception as e:
            return f"Erro: {e}"

    def formatar_relatorio_texto(self):
        d = self.dados_extracao
        return (f"RELATÓRIO GERADO\n{'='*20}\n"
                f"Tipo: {d['Tipo']}\nNota nº: {d['Número']}\nData: {d['Data']}\n"
                f"Frete: R$ {d['Frete (R$)']:.2f}\nImpostos: R$ {d['Impostos (R$)']:.2f}\n"
                f"Total: R$ {d['Total (R$)']:.2f}")

    def exportar_excel(self):
        if not self.dados_extracao: return
        caminho = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx")])
        if caminho:
            df = pd.DataFrame([self.dados_extracao])
            df.to_excel(caminho, index=False)
            messagebox.showinfo("Sucesso", "Excel gerado com sucesso!")

    def exportar_pdf(self):
        if not self.dados_extracao: return
        caminho = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF", "*.pdf")])
        if caminho:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(200, 10, txt="Relatório de Validação Fiscal", ln=True, align='C')
            pdf.set_font("Arial", size=12)
            pdf.ln(10)
            for chave, valor in self.dados_extracao.items():
                pdf.cell(200, 10, txt=f"{chave}: {valor}", ln=True)
            pdf.output(caminho)
            messagebox.showinfo("Sucesso", "PDF gerado com sucesso!")

# --- INTERFACE ---
app_logic = ValidadorFiscal()

def acao_validar():
    tipo = combo_tipo.get()
    arquivo = filedialog.askopenfilename(filetypes=[("XML", "*.xml")])
    if arquivo:
        res = app_logic.processar_xml(arquivo, tipo)
        text_area.delete(1.0, tk.END)
        text_area.insert(tk.END, res)
        btn_excel.config(state="normal")
        btn_pdf.config(state="normal")

janela = tk.Tk()
janela.title("Validador Fiscal Interno")
janela.geometry("450x550")

tk.Label(janela, text="Selecione o Tipo de Nota:", font=("Arial", 10, "bold")).pack(pady=10)
combo_tipo = ttk.Combobox(janela, values=["NF-e", "NFC-e", "NFS-e", "CT-e", "MDF-e"], state="readonly")
combo_tipo.current(0)
combo_tipo.pack()

tk.Button(janela, text="Selecionar XML", command=acao_validar, bg="#2196F3", fg="white").pack(pady=20)

text_area = tk.Text(janela, height=8, width=50)
text_area.pack(pady=10)

frame_botoes = tk.Frame(janela)
frame_botoes.pack(pady=10)

btn_excel = tk.Button(frame_botoes, text="Exportar Excel", command=app_logic.exportar_excel, state="disabled", bg="#4CAF50", fg="white")
btn_excel.pack(side="left", padx=5)

btn_pdf = tk.Button(frame_botoes, text="Exportar PDF", command=app_logic.exportar_pdf, state="disabled", bg="#F44336", fg="white")
btn_pdf.pack(side="left", padx=5)

janela.mainloop()