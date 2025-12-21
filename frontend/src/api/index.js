// frontend/src/api/index.js
import axios from 'axios';

// Get the API base URL from the environment variable provided by Vite
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api';

// Create a single, configured axios instance
const apiClient = axios.create({
  baseURL: API_BASE_URL,
});

// Use an interceptor to dynamically add the Authorization header
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

export default apiClient;