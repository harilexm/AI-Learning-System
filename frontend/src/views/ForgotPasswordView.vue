<template>
  <div class="container">
    <form @submit.prevent="handleRequest" class="form">
      <h2>Forgot Password</h2>
      <p>Enter your email address and we will send you a link to reset your password.</p>
      <div class="form-group">
        <label for="email">Email</label>
        <input type="email" id="email" v-model="email" required />
      </div>
      <button type="submit" :disabled="isLoading">{{ isLoading ? 'Sending...' : 'Send Reset Link' }}</button>
      <p v-if="message" class="message">{{ message }}</p>
    </form>
  </div>
</template>
<script setup>
import { ref } from 'vue';
import axios from 'axios';
const email = ref('');
const message = ref('');
const isLoading = ref(false);
const handleRequest = async () => {
  isLoading.value = true;
  message.value = '';
  try {
    const response = await axios.post('http://localhost:5000/api/auth/forgot-password', { email: email.value });
    message.value = response.data.message;
  } catch (error) {
    message.value = 'An error occurred. Please try again.';
  } finally {
    isLoading.value = false;
  }
};
</script>
<style scoped>
/* You can share styles with LoginView */
.container { display: flex; justify-content: center; align-items: center; min-height: 80vh; }
.form { padding: 2rem; background: white; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); width: 100%; max-width: 400px; }
p { color: #6c757d; }
.message { margin-top: 1rem; color: #155724; text-align: center; }
</style>