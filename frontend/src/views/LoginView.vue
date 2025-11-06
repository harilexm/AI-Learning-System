<template>
  <div class="login-container">
    <form @submit.prevent="handleLogin" class="login-form">
      <h2>Log In</h2>
      <div class="form-group">
        <label for="email">Email</label>
        <input type="email" id="email" v-model="email" required />
      </div>
      <div class="form-group">
        <label for="password">Password</label>
        <input type="password" id="password" v-model="password" required />
      </div>
      <button type="submit">Log In</button>
      <p v-if="errorMessage" class="error-message">{{ errorMessage }}</p>
      <div class="extra-links">
        <RouterLink to="/forgot-password">Forgot Password?</RouterLink>
      </div>
    </form>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';

const email = ref('');
const password = ref('');
const errorMessage = ref('');
const router = useRouter();
const authStore = useAuthStore();

const handleLogin = async () => {
  errorMessage.value = '';
  try {
    // Log the user in. This fetches the user's profile and roles.
    await authStore.login(email.value, password.value);
    
    // Check the user's role from the auth store and redirect accordingly.
    if (authStore.isAdmin) {
      router.push('/admin');
    } else if (authStore.isTeacher) {
      router.push('/teacher-dashboard');
    } else {
      router.push('/dashboard'); // Default for students
    }

  } catch (error) {
    errorMessage.value = error.message;
  }
};
</script>

<style scoped>
.login-container {
  display: flex; justify-content: center; align-items: center;
  min-height: calc(100vh - 80px);
  background-color: #f8f9fa;
}
.login-form {
  padding: 2rem; background: white; border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15); width: 100%; max-width: 400px;
}
h2 {
  margin-top: 0;
  margin-bottom: 1.5rem;
  text-align: center;
  color: #333;
}
.form-group { margin-bottom: 1.25rem; }
label {
  display: block; margin-bottom: 0.5rem; font-weight: 500; color: #555;
}
input {
  width: 100%; padding: 0.75rem; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box;
}
input:focus {
  border-color: #28a745; outline: none; box-shadow: 0 0 0 2px rgba(40, 167, 69, 0.25);
}
button {
  width: 100%; padding: 0.75rem; border: none; border-radius: 4px;
  background-color: #28a745; color: white; font-size: 1rem; font-weight: bold; cursor: pointer; transition: background-color 0.2s;
}
button:hover { background-color: #218838; }
.error-message {
  color: #dc3545;
  background-color: #f8d7da;
  border: 1px solid #f5c6cb;
  padding: 0.75rem;
  border-radius: 4px;
  margin-top: 1rem;
  text-align: center;
}
.extra-links { margin-top: 1rem; text-align: center; }
</style>