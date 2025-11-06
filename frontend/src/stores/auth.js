import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import axios from 'axios';

// configured axios instance for authenticated requests
const apiClient = axios.create({
  baseURL: 'http://localhost:5000/api',
});

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const useAuthStore = defineStore('auth', () => {
  // State
  const token = ref(localStorage.getItem('token') || null);
  const user = ref(JSON.parse(localStorage.getItem('user')) || null);

  // Getters
  const isAuthenticated = computed(() => !!token.value);
  const userRoles = computed(() => user.value?.roles || []);
  const isAdmin = computed(() => userRoles.value.includes('administrator'));
  const isTeacher = computed(() => userRoles.value.includes('teacher'));
  const isStudent = computed(() => userRoles.value.includes('student'));

  // Actions
  async function login(email, password) {
    try {
      const response = await axios.post('http://localhost:5000/api/auth/login', {
        email,
        password,
      });

      const newToken = response.data.access_token;
      token.value = newToken;
      localStorage.setItem('token', newToken);

      // After getting the token, immediately fetch the user's profile
      await fetchProfile();
      
      return 'success';
    } catch (error) {
      logout(); // Clear any lingering state on failure
      console.error('Login failed:', error);
      throw new Error(error.response?.data?.error || 'Login failed');
    }
  }

  async function fetchProfile() {
    if (!token.value) return;
    try {
      const response = await apiClient.get('/profile');
      user.value = response.data;
      localStorage.setItem('user', JSON.stringify(response.data));
    } catch (error) {
      console.error('Failed to fetch profile:', error);
      // If fetching fails (e.g expired token) log the user out
      logout();
    }
  }

  function logout() {
    token.value = null;
    user.value = null;
    localStorage.removeItem('token');
    localStorage.removeItem('user');
  }

  return { token, user, isAuthenticated, userRoles, isAdmin, isTeacher, isStudent, login, fetchProfile, logout };
});