from flask import Flask, render_template, request, jsonify, send_file
import tempfile, os, io, uuid, shutil
import xml.etree.ElementTree as ET

# Importa a lógica do arquivo app.py que está na mesma pasta
from validador_fiscal import ValidadorFiscal 

app = Flask(__name__, static_folder='static', template_folder='templates')

# In-memory store for processed results: id -> notas list
STORE = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/validate', methods=['POST'])
def validate():
    try:
        tipo = request.form.get('tipo', 'NF-e')
        files = request.files.getlist('files')
        if not files:
            app.logger.warning('Nenhum arquivo enviado na requisição')
            return jsonify({'error':'Nenhum arquivo enviado'}), 400

        tmpdir = tempfile.mkdtemp(prefix='val_')
        paths = []
        for f in files:
            # some browsers send directories with full path, we just save
            filename = os.path.basename(f.filename) or str(uuid.uuid4()) + '.xml'
            dest = os.path.join(tmpdir, filename)
            f.save(dest)
            paths.append(dest)

        validator = ValidadorFiscal()
        events_index = validator.build_events_index(paths)

        notas = []
        for p in paths:
            try:
                tree = ET.parse(p)
                root = tree.getroot()
                is_nota = any(validator.limpar_tag(el.tag).lower() == 'infnfe' for el in root.iter())
                if is_nota:
                    try:
                        dados = validator.extrair_dados_xml(p, tipo, events_index=events_index)
                        notas.append(dados)
                    except Exception:
                        app.logger.exception('Erro extraindo dados de: %s', p)
                        continue
            except Exception:
                app.logger.exception('Erro parseando XML: %s', p)
                continue

        # store and return id
        key = str(uuid.uuid4())
        STORE[key] = notas

        # cleanup files
        try:
            shutil.rmtree(tmpdir)
        except Exception:
            app.logger.exception('Erro limpando tmpdir')

        return jsonify({'id': key, 'count': len(notas), 'notas': notas})
    except Exception as e:
        app.logger.exception('Erro na rota /validate')
        return jsonify({'error': 'Erro interno no servidor', 'detail': str(e)}), 500

def build_excel_bytes(notas):
    # Build an Excel in memory similar to desktop exporter
    import xlsxwriter
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    worksheet = workbook.add_worksheet('Notas')
    header_format = workbook.add_format({'bold': True, 'bg_color': '#DCE6F1'})
    money_fmt = workbook.add_format({'num_format': '#,##0.00'})

    headers = ['Tipo','Data','Número','Natureza de Operação','Status','Frete','Impostos','Total','Código Produto','Produto','CFOP','Valor Produto','Imposto Produto']
    for c, h in enumerate(headers):
        worksheet.write(0, c, h, header_format)

    row_idx = 1
    rows = []
    for nota in notas:
        rows.append({'row': {
            'Tipo': nota.get('Tipo',''),
            'Data': nota.get('Data',''),
            'Número': nota.get('Número',''),
            'Natureza de Operação': nota.get('Natureza',''),
            'Status': nota.get('Status',''),
            'Frete': nota.get('Frete (R$)',0.0),
            'Impostos': nota.get('Impostos (R$)',0.0),
            'Total': nota.get('Total (R$)',0.0),
            'Código Produto': '',
            'Produto': '',
            'CFOP': '',
            'Valor Produto': '',
            'Imposto Produto': ''
        }, 'level': 0})
        for p in nota.get('Produtos', []):
            rows.append({'row': {
                'Tipo': '', 'Data': '', 'Número': '', 'Natureza de Operação': '', 'Status':'', 'Frete':'', 'Impostos':'', 'Total':'',
                'Código Produto': p.get('codigo',''), 'Produto': p.get('descricao',''), 'CFOP': p.get('cfop',''), 'Valor Produto': p.get('vProd',0.0), 'Imposto Produto': p.get('imposto',0.0)
            }, 'level': 1})

    for item in rows:
        r = item['row']; lvl = item['level']
        worksheet.write(row_idx, 0, r.get('Tipo',''))
        worksheet.write(row_idx, 1, r.get('Data',''))
        worksheet.write(row_idx, 2, r.get('Número',''))
        worksheet.write(row_idx, 3, r.get('Natureza de Operação',''))
        worksheet.write(row_idx, 4, r.get('Status',''))
        if r.get('Frete','') != '':
            worksheet.write_number(row_idx, 5, float(r.get('Frete',0.0)), money_fmt)
        if r.get('Impostos','') != '':
            worksheet.write_number(row_idx, 6, float(r.get('Impostos',0.0)), money_fmt)
        if r.get('Total','') != '':
            worksheet.write_number(row_idx, 7, float(r.get('Total',0.0)), money_fmt)
        worksheet.write(row_idx, 8, r.get('Código Produto',''))
        worksheet.write(row_idx, 9, r.get('Produto',''))
        worksheet.write(row_idx, 10, r.get('CFOP',''))
        if r.get('Valor Produto','') != '':
            worksheet.write_number(row_idx, 11, float(r.get('Valor Produto',0.0)), money_fmt)
        if r.get('Imposto Produto','') != '':
            worksheet.write_number(row_idx, 12, float(r.get('Imposto Produto',0.0)), money_fmt)

        if lvl == 1:
            worksheet.set_row(row_idx, None, None, {'level': lvl, 'hidden': True})
        else:
            worksheet.set_row(row_idx, None, None, {'level': lvl, 'collapsed': True})
        row_idx += 1

    # total authorized
    total_autorizadas = 0.0
    for nota in notas:
        try:
            if nota.get('Status') != 'Cancelado':
                total_autorizadas += float(nota.get('Total (R$)', nota.get('Total', 0.0) or 0.0))
        except:
            pass
    worksheet.write(row_idx, 6, 'TOTAL AUTORIZADAS', header_format)
    worksheet.write_number(row_idx, 6, total_autorizadas, money_fmt)

    workbook.close()
    output.seek(0)
    return output

@app.route('/download/<key>')
def download(key):
    notas = STORE.get(key)
    if notas is None:
        return 'ID não encontrado', 404
    bio = build_excel_bytes(notas)
    return send_file(bio, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', as_attachment=True, download_name='notas.xlsx')


if __name__ == '__main__':
    # Para desenvolvimento local
    app.run(debug=True, host='0.0.0.0', port=5000)
