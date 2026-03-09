<template>
  <div class="profile-container">
    <h1>My Profile</h1>

    <!-- User Information Card -->
    <div class="card info-card">
      <h2>Account Details</h2>
      <div class="info-grid">
        <div class="info-item">
          <label>Username</label>
          <p>{{ authStore.user?.username }}</p>
        </div>
        <div class="info-item">
          <label>Email</label>
          <p>{{ authStore.user?.email }}</p>
        </div>
        <div class="info-item">
          <label>Role(s)</label>
          <p class="roles">{{ authStore.userRoles.join(', ') }}</p>
        </div>
      </div>
    </div>

    <!-- Change Password Card -->
    <div class="card password-card">
      <h2>Change Password</h2>
      <form @submit.prevent="handleChangePassword">
        <div class="form-group">
          <label for="currentPassword">Current Password</label>
          <input id="currentPassword" v-model="passwords.current_password" type="password" required />
        </div>
        <div class="form-group">
          <label for="newPassword">New Password</label>
          <input id="newPassword" v-model="passwords.new_password" type="password" required />
        </div>
        <div class="form-group">
          <label for="confirmPassword">Confirm New Password</label>
          <input id="confirmPassword" v-model="passwords.confirm_password" type="password" required />
        </div>
        
        <button type="submit" class="btn" :disabled="isLoading">
          {{ isLoading ? 'Saving...' : 'Save New Password' }}
        </button>
      </form>
    </div>
    
    <p v-if="message" class="message" :class="{ 'error': isError }">{{ message }}</p>

  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useAuthStore } from '@/stores/auth';
import apiClient from '@/api';

const authStore = useAuthStore();
const isLoading = ref(false);
const message = ref('');
const isError = ref(false);

const passwords = ref({
  current_password: '',
  new_password: '',
  confirm_password: ''
});

const handleChangePassword = async () => {
  // Frontend validation
  if (passwords.value.new_password !== passwords.value.confirm_password) {
    showMessage('New passwords do not match.', true);
    return;
  }
  if (passwords.value.new_password.length < 8) {
    showMessage('New password must be at least 8 characters long.', true);
    return;
  }

  isLoading.value = true;
  try {
    const response = await apiClient.post('/profile/change-password', {
      current_password: passwords.value.current_password,
      new_password: passwords.value.new_password
    });
    showMessage(response.data.message);
    // Clear form on success
    passwords.value = { current_password: '', new_password: '', confirm_password: '' };
  } catch (err) {
    showMessage(err.response?.data?.error || 'Failed to change password.', true);
  } finally {
    isLoading.value = false;
  }
};

const showMessage = (msg, isErr = false) => {
  message.value = msg;
  isError.value = isErr;
  setTimeout(() => {
    message.value = '';
    isError.value = false;
  }, 5000);
};
</script>

<style scoped>
.profile-container { max-width: 700px; margin: 2rem auto; padding: 1rem;}
.card { background: #fff; padding: 2rem; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); margin-bottom: 2rem;}
.info-card h2, .password-card h2 {margin-top: 0; border-bottom: 1px solid #eee; padding-bottom: 1rem; margin-bottom: 1.5rem;}
.info-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem;}
.info-item label { font-weight: bold; color: #6c757d; display: block; margin-bottom: 0.25rem;}
.info-item p { margin: 0; font-size: 1.1rem;}
.info-item .roles {text-transform: capitalize;}
.form-group { margin-bottom: 1.5rem;}
label { display: block; margin-bottom: 0.5rem; font-weight: 500;}
input { width: 100%; padding: 0.75rem; border: 1px solid #ccc; border-radius: 4px;}
.btn { background-color: #007bff; color: white; padding: 0.75rem 1.5rem; border: none; border-radius: 4px; cursor: pointer;}
.message { padding: 1rem; border-radius: 4px; text-align: center; margin-top: 1rem;}
.message.error { background-color: #f8d7da; color: #721c24; }
.message:not(.error) { background-color: #d4edda; color: #155724; }
</style>