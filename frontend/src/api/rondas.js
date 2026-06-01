import api from './client'

export const login = (login, senha) =>
  api.post('/auth/login', { login, senha }).then((r) => r.data)

export const getSetores = () =>
  api.get('/setores').then((r) => r.data)

export const getRondasHoje = () =>
  api.get('/rondas/hoje').then((r) => r.data)

export const iniciarRonda = (setor_id) =>
  api.post('/rondas', { setor_id }).then((r) => r.data)

export const atualizarRonda = (ronda_id, data) =>
  api.patch(`/rondas/${ronda_id}`, data).then((r) => r.data)

export const gerarQR = (ronda_id) =>
  api.post(`/rondas/${ronda_id}/qr`).then((r) => r.data)

export const getQRImage = (ronda_id, session_id) =>
  api.get(`/rondas/${ronda_id}/qr/image`, { params: { session_id } }).then((r) => r.data)

// Endpoints públicos (sem auth)
export const getQRInfo = (session_id) =>
  api.get(`/rondas/confirm/${session_id}/info`).then((r) => r.data)

export const confirmarQR = (session_id, resposta, device_data) =>
  api.post(`/rondas/confirm/${session_id}`, { resposta, device_data }).then((r) => r.data)
