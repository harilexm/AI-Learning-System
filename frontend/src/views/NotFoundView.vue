<template>
  <div class="not-found-container">
    <h1>404 - Page Not Found</h1>
    <p>The page you are looking for does not exist or has been moved.</p>
    <RouterLink to="/dashboard" class="btn">Go to Dashboard</RouterLink>
  </div>
</template>

<script setup>
import { RouterLink } from 'vue-router';
</script>

<style scoped>
.not-found-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 60vh;
  text-align: center;
  color: #333;
}

h1 {
  font-size: 3rem;
  margin-bottom: 1rem;
  color: #dc3545;
}

p {
  font-size: 1.2rem;
  margin-bottom: 2rem;
}

.btn {
  padding: 0.75rem 1.5rem;
  background-color: #007bff;
  color: white;
  border-radius: 4px;
  text-decoration: none;
  font-weight: bold;
}

.btn:hover {
  background-color: #0056b3;
}
</style>
