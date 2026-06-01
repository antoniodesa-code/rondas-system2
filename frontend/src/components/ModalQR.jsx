import { useEffect, useRef, useState } from 'react'

const POLL_INTERVAL = 3000

export default function ModalQR({ data, onClose, onConfirmado }) {
  const { ronda_id, session_id, url, expires_in, image_b64, setor_nome } = data
  const [timeLeft, setTimeLeft] = useState(expires_in)
  const [confirmed, setConfirmed] = useState(false)
  const timerRef = useRef(null)
  const pollRef = useRef(null)

  // Countdown
  useEffect(() => {
    timerRef.current = setInterval(() => {
      setTimeLeft((t) => {
        if (t <= 1) {
          clearInterval(timerRef.current)
          return 0
        }
        return t - 1
      })
    }, 1000)
    return () => clearInterval(timerRef.current)
  }, [])

  // Poll para detectar confirmação
  useEffect(() => {
    pollRef.current = setInterval(async () => {
      try {
        // Tenta buscar info do QR — se 404, foi usado ou expirou
        const resp = await fetch(`/api/rondas/confirm/${session_id}/info`)
        if (resp.status === 404) {
          clearInterval(pollRef.current)
          setConfirmed(true)
          setTimeout(onConfirmado, 1500)
        }
      } catch {
        // ignora
      }
    }, POLL_INTERVAL)
    return () => clearInterval(pollRef.current)
  }, [session_id, onConfirmado])

  const expired = timeLeft === 0

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-sm text-center">
        <div className="flex items-center justify-between p-5 border-b">
          <h2 className="text-lg font-bold text-gray-800">QR Code — {setor_nome}</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl">✕</button>
        </div>

        <div className="p-6">
          {confirmed ? (
            <div className="py-8">
              <div className="text-6xl mb-3">✅</div>
              <p className="text-green-700 font-bold text-xl">Resposta Registrada!</p>
            </div>
          ) : expired ? (
            <div className="py-8">
              <div className="text-6xl mb-3">⏱️</div>
              <p className="text-red-600 font-bold text-lg">QR Expirado</p>
              <p className="text-gray-500 text-sm mt-2">Feche e gere um novo QR Code.</p>
            </div>
          ) : (
            <>
              {image_b64 ? (
                <img
                  src={`data:image/png;base64,${image_b64}`}
                  alt="QR Code"
                  className="mx-auto w-56 h-56 rounded-lg border-2 border-gray-200"
                />
              ) : (
                <div className="w-56 h-56 mx-auto bg-gray-100 rounded-lg flex items-center justify-center text-gray-400">
                  Gerando QR...
                </div>
              )}

              {/* Timer */}
              <div className={`mt-4 text-2xl font-mono font-bold ${timeLeft <= 30 ? 'text-red-600' : 'text-blue-700'}`}>
                {String(Math.floor(timeLeft / 60)).padStart(2, '0')}:{String(timeLeft % 60).padStart(2, '0')}
              </div>
              <p className="text-gray-500 text-xs mt-1">Aguardando confirmação...</p>

              {/* URL fallback */}
              <p className="mt-3 text-xs text-gray-400 break-all">{url}</p>
            </>
          )}
        </div>

        <div className="p-5 pt-0">
          <button onClick={onClose} className="w-full btn-secondary">
            Fechar
          </button>
        </div>
      </div>
    </div>
  )
}
