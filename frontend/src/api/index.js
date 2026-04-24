import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 120000,
})

export async function createSession(patientInfo = null) {
  const { data } = await api.post('/sessions', { patient_info: patientInfo })
  return data
}

export async function getSession(sessionId) {
  const { data } = await api.get(`/sessions/${sessionId}`)
  return data
}

export async function sendChat(sessionId, message, patientInfo = null) {
  const { data } = await api.post('/chat', {
    session_id: sessionId,
    message,
    patient_info: patientInfo,
  })
  return data
}

export async function runDiagnosis(sessionId, symptoms, duration = '', severity = '', patientInfo = null) {
  const { data } = await api.post('/diagnosis', {
    session_id: sessionId,
    symptoms,
    duration,
    severity_level: severity,
    patient_info: patientInfo,
  })
  return data
}
