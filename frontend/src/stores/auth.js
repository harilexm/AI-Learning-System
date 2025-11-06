// frontend/src/stores/auth.js
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import axios from 'axios'; // Keep for public login/register calls
import apiClient from '@/api'; // Import our new central client

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
      // Login is a public route, so we can use the base axios instance
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
      logout();
      throw new Error(error.response?.data?.error || 'Login failed');
    }
  }

  async function fetchProfile() {
    if (!localStorage.getItem('token')) return;
    try {
      // Use the central apiClient for this authenticated request
      const response = await apiClient.get('/profile');
      user.value = response.data;
      localStorage.setItem('user', JSON.stringify(response.data));
    } catch (error) {
      console.error('Failed to fetch profile:', error);
      logout(); // If fetching fails (e.g., expired token), log the user out
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