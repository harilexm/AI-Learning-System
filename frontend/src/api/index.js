import axios from 'axios';

// Create a single, configured axios instance
const apiClient = axios.create({
  baseURL: 'http://localhost:5000/api',
});

// Use an interceptor to dynamically add the Authorization header to every request
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