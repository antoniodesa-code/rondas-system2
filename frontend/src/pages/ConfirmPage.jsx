import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { confirmarQR, getQRInfo } from '../api/rondas'

function collectDeviceData() {
  return {
    userAgent: navigator.userAgent,
    language: navigator.language,
    platform: navigator.platform,
    hardwareConcurrency: navigator.hardwareConcurrency,
    deviceMemory: navigator.deviceMemory,
    screenWidth: screen.width,
    screenHeight: screen.height,
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
  }
}

export default function ConfirmPage() {
  const { sessionId } = useParams()
  const [info, setInfo] = useState(null)
  const [state, setState] = useState('loading') // loading | ready | done | expired | error
  const [resposta, setResposta] = useState('')

  useEffect(() => {
    getQRInfo(sessionId)
      .then((data) => {
        setInfo(data)
        setState('ready')
      })
      .catch((err) => {
        if (err.response?.status === 404) {
          setState('expired')
        } else {
          setState('error')
        }
      })
  }, [sessionId])

  const handleResponder = async (resp) => {
    setState('loading')
    setResposta(resp)
    try {
      const device_data = collectDeviceData()
      await confirmarQR(sessionId, resp, device_data)
      setState('done')
    } catch (err) {
      if (err.response?.status === 410) {
        setState('expired')
      } else {
        setState('error')
      }
    }
  }

  if (state === 'loading') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-blue-50">
        <div className="text-blue-700 text-lg font-medium">Carregando...</div>
      </div>
    )
  }

  if (state === 'expired') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-red-50 p-4">
        <div className="text-center max-w-sm">
          <div className="text-6xl mb-4">⏱️</div>
          <h2 className="text-2xl font-bold text-red-700 mb-2">QR Code Expirado</h2>
          <p className="text-gray-600">Este código expirou ou já foi utilizado. Solicite um novo QR ao técnico.</p>
        </div>
      </div>
    )
  }

  if (state === 'error') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 p-4">
        <div className="text-center max-w-sm">
          <div className="text-6xl mb-4">⚠️</div>
          <h2 className="text-2xl font-bold text-gray-700 mb-2">Erro</h2>
          <p className="text-gray-600">Ocorreu um erro. Tente novamente.</p>
        </div>
      </div>
    )
  }

  if (state === 'done') {
    const isSimm = resposta === 'sim'
    return (
      <div className={`min-h-screen flex items-center justify-center p-4 ${isSimm ? 'bg-green-50' : 'bg-red-50'}`}>
        <div className="text-center max-w-sm">
          <div className="text-7xl mb-4">{isSimm ? '✅' : '❌'}</div>
          <h2 className={`text-3xl font-bold mb-2 ${isSimm ? 'text-green-700' : 'text-red-700'}`}>
            {isSimm ? 'Confirmado!' : 'Registrado'}
          </h2>
          <p className="text-gray-600 text-lg">Resposta registrada com sucesso.</p>
          {info && (
            <p className="text-gray-500 text-sm mt-3">Setor: {info.setor_nome}</p>
          )}
        </div>
      </div>
    )
  }

  // ready
  return (
    <div className="min-h-screen flex items-center justify-center bg-blue-50 p-4">
      <div className="bg-white rounded-2xl shadow-xl p-8 w-full max-w-sm text-center">
        <div className="text-5xl mb-4">🏥</div>
        <h1 className="text-2xl font-bold text-blue-900 mb-1">Ronda Hospitalar</h1>

        {info && (
          <div className="bg-blue-50 rounded-lg p-3 mb-6 text-sm text-blue-800">
            <p className="font-semibold">{info.setor_nome}</p>
            <p className="text-blue-600">Técnico: {info.tecnico_nome}</p>
          </div>
        )}

        <p className="text-gray-700 text-lg font-medium mb-8">
          O técnico compareceu ao setor?
        </p>

        <div className="flex flex-col gap-4">
          <button
            onClick={() => handleResponder('sim')}
            className="btn-success w-full"
          >
            ✓ SIM
          </button>
          <button
            onClick={() => handleResponder('nao')}
            className="btn-danger w-full"
          >
            ✗ NÃO
          </button>
        </div>
      </div>
    </div>
  )
}
