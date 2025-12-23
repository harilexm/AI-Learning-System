import axios from 'axios';

const apiClient = axios.create({
  // The only change is here: from 'http://localhost:5000/api' to '/api'
  baseURL: '/api', 
});

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