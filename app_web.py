from flask import Flask, request, jsonify, render_template
import xml.etree.ElementTree as ET
from flask import jsonify


app = Flask(__name__)

class ValidadorFiscal:
    def limpar_tag(self, tag):
        return tag.split('}', 1)[1] if '}' in tag else tag

    def buscar_valor(self, root, tags):
        for elemento in root.iter():
            if self.limpar_tag(elemento.tag) in tags:
                return elemento.text
        return "0.00"

    def extrair_dados_xml(self, xml_content, tipo):
        root = ET.fromstring(xml_content)

        numero = self.buscar_valor(root, ['nNF', 'Numero', 'numNota', 'nCT', 'nMDF'])
        data = self.buscar_valor(root, ['dhEmi', 'DataEmissao', 'dEmi', 'dhEmiS'])
        v_nota = self.buscar_valor(root, ['vNF', 'vServ', 'vLiquido', 'vProd', 'vTPrest'])

        return {
            "Tipo": tipo,
            "Número": numero,
            "Data": data,
            "Total": v_nota
        }

validator = ValidadorFiscal()

from flask import render_template

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/validate', methods=['POST'])
def validar():
    try:
        arquivos = request.files.getlist('files')
        notas = []

        for arquivo in arquivos:
            conteudo = arquivo.read()
            dados = validator.extrair_dados_xml(conteudo, "NF-e")
            notas.append(dados)

        return jsonify({
            "notas": notas
        })

    except Exception as e:
        return jsonify({
            "erro": str(e)
        }), 500


if __name__ == '__main__':
    app.run(debug=True)


