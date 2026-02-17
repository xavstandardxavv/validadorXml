const form = document.getElementById('uploadForm')
const filesInput = document.getElementById('files')
const resultArea = document.getElementById('resultArea')
const btnDownload = document.getElementById('btnDownload')
let currentId = null

form.addEventListener('submit', async (e) =>{
  e.preventDefault()
  const files = filesInput.files
  if(!files || files.length===0){ alert('Selecione ao menos um arquivo ou pasta'); return }
  const tipo = document.getElementById('tipo').value
  const fd = new FormData()
  fd.append('tipo', tipo)
  for(let i=0;i<files.length;i++) fd.append('files', files[i])

  resultArea.innerHTML = '<p class="muted">Processando... aguarde</p>'
  btnDownload.disabled = true

  const resp = await fetch('/validate', {method:'POST', body: fd})
  if(!resp.ok){ resultArea.innerHTML = '<p class="muted">Erro ao processar</p>'; return }
  const data = await resp.json()
  currentId = data.id
  btnDownload.disabled = false

  renderResults(data.notas)
})

btnDownload.addEventListener('click', ()=>{
  if(!currentId) return
  window.location = `/download/${currentId}`
})

function renderResults(notas){
  if(!notas || notas.length===0){ resultArea.innerHTML = '<p class="muted">Nenhuma nota encontrada.</p>'; return }
  resultArea.innerHTML = ''
  notas.forEach(n=>{
    const div = document.createElement('div')
    div.className='nota'
    const title = document.createElement('h3')
    title.textContent = `${n.Tipo} • Nº ${n['Número']} • ${n.Data}`
    div.appendChild(title)
    const meta = document.createElement('div')
    meta.innerHTML = `<strong>Status:</strong> ${n.Status || ''} &nbsp; <strong>Natureza:</strong> ${n.Natureza || ''} &nbsp; <strong>Total:</strong> R$ ${Number(n['Total (R$)']||n['Total']||0).toFixed(2)}`
    div.appendChild(meta)

    if(n.Produtos && n.Produtos.length){
      const details = document.createElement('details')
      const summary = document.createElement('summary')
      summary.textContent = `Produtos (${n.Produtos.length})`
      details.appendChild(summary)
      const ul = document.createElement('ul')
      n.Produtos.forEach(p=>{
        const li = document.createElement('li')
        li.innerHTML = `<strong>${p.codigo||''}</strong> — ${p.descricao||''} | CFOP: ${p.cfop||''} | Valor: R$ ${Number(p.vProd||0).toFixed(2)} | Imp: R$ ${Number(p.imposto||0).toFixed(2)}`
        ul.appendChild(li)
      })
      details.appendChild(ul)
      div.appendChild(details)
    }
    resultArea.appendChild(div)
  })
}
