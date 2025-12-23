<template>
  <div class="container">
    <form @submit.prevent="handleReset" class="form">
      <h2>Reset Your Password</h2>
      <div class="form-group">
        <label for="password">New Password</label>
        <input type="password" id="password" v-model="password" required />
      </div>
      <div class="form-group">
        <label for="confirmPassword">Confirm New Password</label>
        <input type="password" id="confirmPassword" v-model="confirmPassword" required />
      </div>
      <button type="submit" :disabled="isLoading">{{ isLoading ? 'Resetting...' : 'Reset Password' }}</button>
      <p v-if="message" class="message" :class="{ 'error': isError }">{{ message }}</p>
    </form>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import axios from 'axios';
const route = useRoute();
const router = useRouter();
const password = ref('');
const confirmPassword = ref('');
const token = ref('');
const message = ref('');
const isError = ref(false);
const isLoading = ref(false);

onMounted(() => {
  token.value = route.query.token;
  if (!token.value) {
    message.value = 'Invalid or missing reset token.';
    isError.value = true;
  }
});

const handleReset = async () => {
  if (password.value !== confirmPassword.value) {
    message.value = 'Passwords do not match.';
    isError.value = true;
    return;
  }
  isLoading.value = true;
  isError.value = false;
  message.value = '';
  try {
    const response = await axios.post('/api/auth/reset-password', { token: token.value, password: password.value });
    message.value = response.data.message + " Redirecting to login...";
    setTimeout(() => router.push('/login'), 3000);
  } catch (error) {
    message.value = error.response?.data?.error || 'An error occurred.';
    isError.value = true;
  } finally {
    isLoading.value = false;
  }
};
</script>

<style scoped>
.container { display: flex; justify-content: center; align-items: center; min-height: 80vh; }
.form { padding: 2rem; background: white; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); width: 100%; max-width: 400px; }
.message { margin-top: 1rem; text-align: center; }
.message.error { color: #dc3545; }
.message:not(.error) { color: #155724; }
</style>