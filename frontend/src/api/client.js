import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

const client = axios.create({
  baseURL: API_BASE,
  timeout: 90000,   // 90 s — cold-start report generation can take 30–40 s on first request
  headers: { 'Content-Type': 'application/json' }
});

export default client;
