import { useCallback, useEffect, useState } from 'react'
import { useAuthStore } from '../store/authStore'
import { atualizarRonda, gerarQR, getQRImage, getRondasHoje, iniciarRonda } from '../api/rondas'
import ModalObs from '../components/ModalObs'
import ModalQR from '../components/ModalQR'

const STATUS_STYLES = {
  pendente: 'bg-yellow-50 border-l-4 border-yellow-400',
  confirmado: 'bg-green-50 border-l-4 border-green-500',
  recusado: 'bg-red-50 border-l-4 border-red-500',
}

const STATUS_BADGE = {
  pendente: 'bg-yellow-100 text-yellow-800',
  confirmado: 'bg-green-100 text-green-800',
  recusado: 'bg-red-100 text-red-800',
}

export default function RondaPage() {
  const { tecnico, logout } = useAuthStore()
  const [rondas, setRondas] = useState([])
  const [loading, setLoading] = useState(true)
  const [iniciando, setIniciando] = useState(false)
  const [modalObs, setModalObs] = useState(null)   // { ronda_id, obs }
  const [modalQR, setModalQR] = useState(null)     // { ronda_id, session_id, url, image_b64 }

  const carregarRondas = useCallback(async () => {
    try {
      const data = await getRondasHoje()
      setRondas(data)
    } catch {
      // token expirado — interceptor redireciona
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    carregarRondas()
  }, [carregarRondas])

  const handleIniciarRonda = async () => {
    setIniciando(true)
    try {
      await iniciarRonda(0) // 0 = todos os setores
      await carregarRondas()
    } finally {
      setIniciando(false)
    }
  }

  const handleRadio = async (ronda_id, field, value) => {
    setRondas((prev) =>
      prev.map((r) => (r.id === ronda_id ? { ...r, [field]: value } : r))
    )
    try {
      const updated = await atualizarRonda(ronda_id, { [field]: value })
      setRondas((prev) => prev.map((r) => (r.id === ronda_id ? { ...r, ...updated } : r)))
    } catch {
      // reverter em caso de erro
      await carregarRondas()
    }
  }

  const handleSalvarObs = async (ronda_id, observacao) => {
    try {
      const updated = await atualizarRonda(ronda_id, { observacao })
      setRondas((prev) => prev.map((r) => (r.id === ronda_id ? { ...r, ...updated } : r)))
    } finally {
      setModalObs(null)
    }
  }

  const handleAbrirQR = async (ronda) => {
    try {
      const qrData = await gerarQR(ronda.id)
      const imgData = await getQRImage(ronda.id, qrData.session_id)
      setModalQR({
        ronda_id: ronda.id,
        session_id: qrData.session_id,
        url: qrData.url,
        expires_in: qrData.expires_in,
        image_b64: imgData.image_b64,
        setor_nome: ronda.setor_nome,
      })
    } catch {
      alert('Erro ao gerar QR Code')
    }
  }

  const handleQRConfirmado = async () => {
    setModalQR(null)
    await carregarRondas()
  }

  const hoje = new Date().toLocaleDateString('pt-BR', { weekday: 'long', day: '2-digit', month: 'long' })

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-blue-900 text-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold">🏥 Ronda Hospitalar</h1>
            <p className="text-blue-300 text-xs capitalize">{hoje}</p>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-blue-200 text-sm hidden sm:block">{tecnico?.nome}</span>
            <button onClick={logout} className="text-blue-300 hover:text-white text-sm underline">
              Sair
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-2 sm:px-4 py-6">
        {/* Ação principal */}
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-800">
            {rondas.length > 0 ? `${rondas.length} setores` : 'Nenhuma ronda iniciada'}
          </h2>
          {rondas.length === 0 && !loading && (
            <button
              onClick={handleIniciarRonda}
              disabled={iniciando}
              className="btn-primary"
            >
              {iniciando ? 'Iniciando...' : '+ Iniciar Ronda de Hoje'}
            </button>
          )}
          {rondas.length > 0 && (
            <button onClick={carregarRondas} className="btn-secondary text-sm">
              Atualizar
            </button>
          )}
        </div>

        {loading && (
          <div className="text-center py-16 text-gray-400">Carregando...</div>
        )}

        {/* Tabela desktop */}
        {!loading && rondas.length > 0 && (
          <>
            {/* Desktop */}
            <div className="hidden md:block bg-white rounded-xl shadow overflow-hidden">
              <table className="w-full text-sm">
                <thead className="bg-blue-900 text-white">
                  <tr>
                    <th className="px-4 py-3 text-left font-semibold w-1/4">SETOR</th>
                    <th className="px-4 py-3 text-center font-semibold">SISTEMA</th>
                    <th className="px-4 py-3 text-center font-semibold">USUÁRIO</th>
                    <th className="px-4 py-3 text-center font-semibold">OBS</th>
                    <th className="px-4 py-3 text-center font-semibold">QR</th>
                    <th className="px-4 py-3 text-center font-semibold">STATUS</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {rondas.map((ronda) => (
                    <tr key={ronda.id} className={`${STATUS_STYLES[ronda.status]} transition-colors`}>
                      <td className="px-4 py-3 font-semibold text-gray-800">{ronda.setor_nome}</td>

                      {/* Sistema */}
                      <td className="px-4 py-3">
                        <div className="flex justify-center gap-3">
                          <RadioBtn
                            label="Sim"
                            checked={ronda.sistema_operante === true}
                            onChange={() => handleRadio(ronda.id, 'sistema_operante', true)}
                            color="green"
                          />
                          <RadioBtn
                            label="Não"
                            checked={ronda.sistema_operante === false}
                            onChange={() => handleRadio(ronda.id, 'sistema_operante', false)}
                            color="red"
                          />
                        </div>
                      </td>

                      {/* Usuário */}
                      <td className="px-4 py-3">
                        <div className="flex justify-center gap-3">
                          <RadioBtn
                            label="Sim"
                            checked={ronda.usuario_utilizando === true}
                            onChange={() => handleRadio(ronda.id, 'usuario_utilizando', true)}
                            color="green"
                          />
                          <RadioBtn
                            label="Não"
                            checked={ronda.usuario_utilizando === false}
                            onChange={() => handleRadio(ronda.id, 'usuario_utilizando', false)}
                            color="red"
                          />
                        </div>
                      </td>

                      {/* OBS */}
                      <td className="px-4 py-3 text-center">
                        <button
                          onClick={() => setModalObs({ ronda_id: ronda.id, obs: ronda.observacao || '' })}
                          className={`px-3 py-1 rounded-lg text-xs font-medium border transition-colors ${
                            ronda.observacao
                              ? 'bg-orange-100 text-orange-700 border-orange-300'
                              : 'bg-gray-100 text-gray-600 border-gray-300 hover:bg-gray-200'
                          }`}
                        >
                          {ronda.observacao ? '📝 Ver' : '+ OBS'}
                        </button>
                      </td>

                      {/* QR */}
                      <td className="px-4 py-3 text-center">
                        <button
                          onClick={() => handleAbrirQR(ronda)}
                          className="bg-blue-100 text-blue-700 border border-blue-300 px-3 py-1 rounded-lg text-xs font-medium hover:bg-blue-200 transition-colors"
                        >
                          📷 QR
                        </button>
                      </td>

                      {/* Status */}
                      <td className="px-4 py-3 text-center">
                        <span className={`px-2 py-1 rounded-full text-xs font-semibold uppercase ${STATUS_BADGE[ronda.status]}`}>
                          {ronda.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Mobile cards */}
            <div className="md:hidden space-y-3">
              {rondas.map((ronda) => (
                <MobileCard
                  key={ronda.id}
                  ronda={ronda}
                  onRadio={handleRadio}
                  onObs={() => setModalObs({ ronda_id: ronda.id, obs: ronda.observacao || '' })}
                  onQR={() => handleAbrirQR(ronda)}
                />
              ))}
            </div>
          </>
        )}
      </main>

      {/* Modals */}
      {modalObs && (
        <ModalObs
          ronda_id={modalObs.ronda_id}
          initialObs={modalObs.obs}
          onSave={handleSalvarObs}
          onClose={() => setModalObs(null)}
        />
      )}

      {modalQR && (
        <ModalQR
          data={modalQR}
          onClose={() => setModalQR(null)}
          onConfirmado={handleQRConfirmado}
        />
      )}
    </div>
  )
}

function RadioBtn({ label, checked, onChange, color }) {
  const colors = {
    green: checked ? 'bg-green-600 text-white border-green-600' : 'border-gray-300 text-gray-600 hover:border-green-400',
    red: checked ? 'bg-red-600 text-white border-red-600' : 'border-gray-300 text-gray-600 hover:border-red-400',
  }
  return (
    <button
      onClick={onChange}
      className={`px-3 py-1 rounded-lg border text-xs font-semibold transition-all ${colors[color]}`}
    >
      {label}
    </button>
  )
}

function MobileCard({ ronda, onRadio, onObs, onQR }) {
  return (
    <div className={`${STATUS_STYLES[ronda.status]} bg-white rounded-xl shadow p-4`}>
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-bold text-gray-800">{ronda.setor_nome}</h3>
        <span className={`px-2 py-0.5 rounded-full text-xs font-semibold uppercase ${STATUS_BADGE[ronda.status]}`}>
          {ronda.status}
        </span>
      </div>

      <div className="grid grid-cols-2 gap-2 text-sm mb-3">
        <div>
          <p className="text-gray-500 text-xs mb-1">SISTEMA</p>
          <div className="flex gap-2">
            <RadioBtn label="Sim" checked={ronda.sistema_operante === true} onChange={() => onRadio(ronda.id, 'sistema_operante', true)} color="green" />
            <RadioBtn label="Não" checked={ronda.sistema_operante === false} onChange={() => onRadio(ronda.id, 'sistema_operante', false)} color="red" />
          </div>
        </div>
        <div>
          <p className="text-gray-500 text-xs mb-1">USUÁRIO</p>
          <div className="flex gap-2">
            <RadioBtn label="Sim" checked={ronda.usuario_utilizando === true} onChange={() => onRadio(ronda.id, 'usuario_utilizando', true)} color="green" />
            <RadioBtn label="Não" checked={ronda.usuario_utilizando === false} onChange={() => onRadio(ronda.id, 'usuario_utilizando', false)} color="red" />
          </div>
        </div>
      </div>

      <div className="flex gap-2">
        <button onClick={onObs} className={`flex-1 py-2 rounded-lg text-xs font-medium border ${ronda.observacao ? 'bg-orange-100 text-orange-700 border-orange-300' : 'bg-gray-100 text-gray-600 border-gray-200'}`}>
          {ronda.observacao ? '📝 OBS' : '+ OBS'}
        </button>
        <button onClick={onQR} className="flex-1 py-2 rounded-lg text-xs font-medium border bg-blue-100 text-blue-700 border-blue-300">
          📷 QR Code
        </button>
      </div>
    </div>
  )
}
