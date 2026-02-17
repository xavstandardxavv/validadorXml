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

@app.route('/validar', methods=['POST'])
def validar():
    try:
        # sua lógica aqui
        return jsonify({"sucesso": True, "mensagem": "Processado com sucesso"})
    
    except Exception as e:
        return jsonify({"sucesso": False, "erro": str(e)}), 500


@app.route('/validar', methods=['POST'])
def validar():
    file = request.files.get('xml')
    tipo = request.form.get('tipo', 'NF-e')

    if not file:
        return jsonify({"erro": "Nenhum XML enviado"}), 400

    xml_content = file.read()
    dados = validator.extrair_dados_xml(xml_content, tipo)

    return jsonify(dados)
