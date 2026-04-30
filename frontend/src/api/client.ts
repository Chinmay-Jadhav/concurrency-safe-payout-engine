import axios from 'axios'
import { v4 as uuidv4 } from 'uuid'

export const api = axios.create({ baseURL: '/api/v1' })
export const generateIdempotencyKey = () => uuidv4()