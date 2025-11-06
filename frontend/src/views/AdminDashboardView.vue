<template>
  <div class="admin-container">
    <h1>User Management</h1>

    <!-- Create User Form -->
    <div class="form-card">
      <h2>Create New User</h2>
      <form @submit.prevent="createUser">
        <div class="form-grid">
          <div class="form-group">
            <label for="firstName">First Name</label>
            <input id="firstName" v-model="newUser.firstName" type="text" required />
          </div>
          <div class="form-group">
            <label for="lastName">Last Name</label>
            <input id="lastName" v-model="newUser.lastName" type="text" required />
          </div>
          <div class="form-group">
            <label for="username">Username</label>
            <input id="username" v-model="newUser.username" type="text" required />
          </div>
          <div class="form-group">
            <label for="email">Email</label>
            <input id="email" v-model="newUser.email" type="email" required />
          </div>
          <div class="form-group">
            <label for="password">Password</label>
            <input id="password" v-model="newUser.password" type="password" required />
          </div>
          <div class="form-group">
            <label for="role">Role</label>
            <select id="role" v-model="newUser.role" required>
              <option value="teacher">Teacher</option>
              <option value="administrator">Administrator</option>
            </select>
          </div>
        </div>
        <button type="submit" class="btn-create">Create User</button>
      </form>
    </div>

    <!-- User List -->
    <h2>Existing Users</h2>
    <div v-if="isLoading">Loading users...</div>
    <div v-if="error" class="error-message">{{ error }}</div>
    
    <p v-if="message" class="success-message">{{ message }}</p>

    <table class="user-table" v-if="users.length">
      <thead>
        <tr>
          <th>Name</th>
          <th>Username</th>
          <th>Email</th>
          <th>Role(s)</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="user in users" :key="user.id">
          <td>{{ user.first_name }} {{ user.last_name }}</td>
          <td>{{ user.username }}</td>
          <td>{{ user.email }}</td>
          <td>{{ user.roles.join(', ') }}</td>
          <td>
            <button @click="deleteUser(user.id)" class="btn-delete">Delete</button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import apiClient from '@/api';

const users = ref([]);
const isLoading = ref(true);
const error = ref('');
const message = ref(''); // For success/error messages

const newUser = ref({
  firstName: '',
  lastName: '',
  username: '',
  email: '',
  password: '',
  role: 'teacher'
});

const fetchUsers = async () => {
  isLoading.value = true;
  error.value = '';
  try {
    const response = await apiClient.get('/admin/users');
    users.value = response.data;
  } catch (err) {
    error.value = err.response?.data?.error || 'Failed to fetch users.';
  } finally {
    isLoading.value = false;
  }
};

const createUser = async () => {
  message.value = '';
  try {
    const response = await apiClient.post('/admin/users', newUser.value);
    message.value = response.data.message;
    // Reset form and refresh user list
    Object.keys(newUser.value).forEach(key => newUser.value[key] = '');
    newUser.value.role = 'teacher';
    await fetchUsers();
  } catch (err) {
    message.value = `Error: ${err.response?.data?.error || 'Could not create user.'}`;
  }
};

const deleteUser = async (userId) => {
  if (!confirm('Are you sure you want to delete this user? This action cannot be undone.')) {
    return;
  }
  message.value = '';
  try {
    const response = await apiClient.delete(`/admin/users/${userId}`);
    message.value = response.data.message;
    await fetchUsers(); // Refresh the list
  } catch (err) {
    message.value = `Error: ${err.response?.data?.error || 'Could not delete user.'}`;
  }
};

onMounted(fetchUsers);
</script>

<style scoped>
.admin-container {
  max-width: 1000px;
  margin: 2rem auto;
  padding: 2rem;
}
.form-card {
  background: #fff;
  padding: 2rem;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  margin-bottom: 2rem;
}
.form-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1.5rem;
  margin-bottom: 1.5rem;
}
.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
}
.form-group input, .form-group select {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ccc;
  border-radius: 4px;
}
.btn-create {
  background-color: #007bff;
  color: white;
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}
.user-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 1rem;
}
.user-table th, .user-table td {
  border: 1px solid #ddd;
  padding: 0.8rem;
  text-align: left;
}
.user-table th {
  background-color: #f8f9fa;
}
.btn-delete {
  background-color: #dc3545;
  color: white;
  padding: 0.4rem 0.8rem;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}
.error-message, .success-message {
  padding: 1rem;
  border-radius: 4px;
  margin-bottom: 1rem;
}
.error-message { background-color: #f8d7da; color: #721c24; }
.success-message { background-color: #d4edda; color: #155724; }
</style>