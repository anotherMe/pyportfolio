
import api from './api'

export async function getAllInstruments() {
  const response = await api.get('/api/instruments')
  return response.data
}
