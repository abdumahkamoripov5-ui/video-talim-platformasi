import axios from 'axios';

export const API_BASE = (import.meta.env.VITE_API_URL || '/api').replace(/\/$/, '');
export const mediaUrl = (path) => {
  if (!path) return '';
  if (/^https?:\/\//.test(path)) return path;
  const origin = API_BASE.startsWith('http') ? new URL(API_BASE).origin : window.location.origin;
  return new URL(path, origin).href;
};
export const clearSession = () => {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
};
export const deviceInfo = () => {
  let id = localStorage.getItem('device_id');
  if (!id) { id = crypto.randomUUID(); localStorage.setItem('device_id', id); }
  return { device_id: id, device_name: navigator.userAgent.match(/\(([^)]+)\)/)?.[1]?.slice(0, 100) || 'Veb brauzer' };
};
const api = axios.create({ baseURL: API_BASE, withCredentials: true, timeout: 20000 });
api.interceptors.request.use(config => {
  const token = localStorage.getItem('access_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});
let refreshing;
api.interceptors.response.use(response => {
  if (response.config.responseType !== 'blob' && response.headers['content-type']?.includes('text/html')) {
    return Promise.reject(new Error('Backend API manzili sozlanmagan.'));
  }
  return response;
}, async error => {
  const original = error.config;
  if (error.response?.status !== 401 || !original || original._retry || original.url?.includes('/auth/')) return Promise.reject(error);
  original._retry = true;
  const refresh = localStorage.getItem('refresh_token');
  if (!refresh) return Promise.reject(error);
  try {
    if (!refreshing) refreshing = axios.post(`${API_BASE}/users/auth/refresh/`, { refresh }, { withCredentials: true })
      .then(({ data }) => {
        localStorage.setItem('access_token', data.access);
        if (data.refresh) localStorage.setItem('refresh_token', data.refresh);
        return data.access;
      }).finally(() => { refreshing = null; });
    const access = await refreshing;
    original.headers.Authorization = `Bearer ${access}`;
    return api(original);
  } catch (refreshError) {
    clearSession();
    window.location.assign('/login');
    return Promise.reject(refreshError);
  }
});
export async function downloadFile(path, filename) {
  const response = await api.get(path.replace(/^\/api/, ''), { responseType: 'blob', params: { download_url: '1' } });
  if (response.data.type.includes('application/json')) {
    const result = JSON.parse(await response.data.text());
    if (!result.download_url) throw new Error('Fayl havolasi olinmadi');
    // Navigate to the signed attachment without sending API tokens or cookies.
    const link = document.createElement('a');
    link.href = result.download_url; link.download = filename;
    link.referrerPolicy = 'no-referrer';
    link.click();
    return;
  }
  const url = URL.createObjectURL(response.data);
  const link = document.createElement('a');
  link.href = url; link.download = filename;
  link.click(); setTimeout(() => URL.revokeObjectURL(url), 10000);
}
export default api;
