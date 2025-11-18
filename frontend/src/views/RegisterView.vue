<template>
  <div class="register-container">
    <form @submit.prevent="handleRegister" class="register-form">
      <h2>Create Your Account</h2>
      
      <div class="form-group">
        <label for="firstName">First Name</label>
        <input type="text" id="firstName" v-model="firstName" required />
      </div>
      
      <div class="form-group">
        <label for="lastName">Last Name</label>
        <input type="text" id="lastName" v-model="lastName" required />
      </div>
      
      <div class="form-group">
        <label for="username">Username</label>
        <input type="text" id="username" v-model="username" required />
      </div>
      
      <div class="form-group">
        <label for="email">Email</label>
        <input type="email" id="email" v-model="email" required />
      </div>
      
      <div class="form-group">
        <label for="password">Password</label>
        <input type="password" id="password" v-model="password" required />
      </div>
      
      <button type="submit">Register</button>
      
      <p v-if="errorMessage" class="error-message">{{ errorMessage }}</p>
      <p v-if="successMessage" class="success-message">{{ successMessage }}</p>
    </form>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import axios from 'axios';

const firstName = ref('');
const lastName = ref('');
const username = ref('');
const email = ref('');
const password = ref('');
const errorMessage = ref('');
const successMessage = ref('');

const handleRegister = async () => {
  errorMessage.value = '';
  successMessage.value = '';

  try {
    const response = await axios.post('http://localhost:5000/api/auth/register', {
      firstName: firstName.value,
      lastName: lastName.value,
      username: username.value,
      email: email.value,
      password: password.value,
    });

    successMessage.value = response.data.message;

    firstName.value = '';
    lastName.value = '';
    username.value = '';
    email.value = '';
    password.value = '';
  } catch (error) {
    if (error.response) {
      errorMessage.value = error.response.data.error || 'Registration failed.';
    } else {
      errorMessage.value = 'Could not connect to the server.';
    }
    console.error('Registration error:', error);
  }
};
</script>

<style scoped>
.register-container {display: flex; justify-content: center; align-items: center; min-height: 80vh; background-color: #f0f2f5; padding: 1rem;}
.register-form { padding: 2rem; background: white; border-radius: 8px; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15); width: 100%; max-width: 400px; }
h2 {margin-top: 0; margin-bottom: 1.5rem; text-align: center; color: #333;}
.form-group { margin-bottom: 1.25rem;}
label { display: block; margin-bottom: 0.5rem; font-weight: 500; color: #555;}
input { width: 100%; padding: 0.75rem; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box;}
input:focus { border-color: #007bff; outline: none; box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);}
button { width: 100%; padding: 0.75rem; border: none; border-radius: 4px; background-color: #007bff; color: white; font-size: 1rem; font-weight: bold; cursor: pointer; transition: background-color 0.2s; }
button:hover { background-color: #0056b3; }
.error-message { color: #dc3545; background-color: #f8d7da; border: 1px solid #f5c6cb; padding: 0.75rem; border-radius: 4px; margin-top: 1rem; text-align: center;}
.success-message {color: #155724; background-color: #d4edda; border: 1px solid #c3e6cb; padding: 0.75rem; border-radius: 4px; margin-top: 1rem; text-align: center;}
</style>