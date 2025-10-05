import axios from 'axios';

const baseURL = (import.meta as any).env?.VITE_API_BASE ?? '/api';
axios.defaults.baseURL = baseURL;

export default axios;
