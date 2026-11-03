import { create } from 'zustand';
import api, { clearSession, deviceInfo } from '../api/axios';

const useAuthStore = create((set, get) => ({
  user: null,
  isAuthenticated: !!localStorage.getItem('access_token'),
  loading: false,
  login: async (email, password) => {
    set({ loading: true });
    try {
      const { data } = await api.post('/users/auth/login/', { email, password, ...deviceInfo() });
      localStorage.setItem('access_token', data.access);
      localStorage.setItem('refresh_token', data.refresh);
      set({ isAuthenticated: true });
      await get().fetchProfile();
      return data;
    } finally { set({ loading: false }); }
  },
  register: async (form) => {
    set({ loading: true });
    try {
      const { data } = await api.post('/users/auth/register/', { ...form, ...deviceInfo() });
      localStorage.setItem('access_token', data.access);
      localStorage.setItem('refresh_token', data.refresh);
      set({ user: data.user, isAuthenticated: true });
      return data;
    } finally { set({ loading: false }); }
  },
  logout: async () => {
    const access = localStorage.getItem('access_token');
    clearSession(); set({ user: null, isAuthenticated: false });
    try { await api.post('/users/auth/logout/', {}, { headers: { Authorization: `Bearer ${access}` } }); } catch { /* Local logout remains available offline. */ }
  },
  fetchProfile: async () => {
    try { const { data } = await api.get('/users/profile/'); set({ user: data }); }
    catch (error) { if (error.response?.status === 401) { clearSession(); set({ user: null, isAuthenticated: false }); } }
  },
}));
export default useAuthStore;
