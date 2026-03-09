<template>
  <div class="admin-container">
    <h1>Admin Panel</h1>

    <!-- System Analytics Section -->
    <div class="analytics-section">
      <h2>System Analytics</h2>
      <div v-if="isLoadingStats" class="loading">Loading platform stats...</div>
      <div v-else>
        <div class="stats-grid">
          <div class="stat-card">
            <div class="stat-value">{{ stats.total_users }}</div>
            <div class="stat-label">Total Users</div>
            <div class="stat-breakdown">
              {{ stats.student_count }} students, {{ stats.teacher_count }} teachers, {{ stats.admin_count }} admins
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-value">{{ stats.total_courses }}</div>
            <div class="stat-label">Courses</div>
            <div class="stat-breakdown">{{ stats.total_content }} content items</div>
          </div>
          <div class="stat-card">
            <div class="stat-value">{{ stats.total_quiz_attempts }}</div>
            <div class="stat-label">Quiz Attempts</div>
          </div>
          <div class="stat-card">
            <div class="stat-value" :class="{'text-success': stats.avg_quiz_score >= 70, 'text-danger': stats.avg_quiz_score < 70}">
              {{ stats.avg_quiz_score }}%
            </div>
            <div class="stat-label">Platform Avg Score</div>
          </div>
        </div>

        <!-- Most Popular Courses -->
        <div v-if="stats.top_courses && stats.top_courses.length > 0" class="top-courses">
          <h3>Most Popular Courses</h3>
          <div class="top-courses-list">
            <div v-for="(c, idx) in stats.top_courses" :key="idx" class="top-course-item">
              <span class="top-rank">#{{ idx + 1 }}</span>
              <span class="top-title">{{ c.title }}</span>
              <span class="top-enrollments">{{ c.enrollments }} enrolled</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- User Management Section -->
    <h2>User Management</h2>
    
    <!-- Create User Form -->
    <div class="form-card">
      <h3>Create New User</h3>
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

    <h3>Existing Users</h3>
    <div v-if="isLoading" class="loading">Loading users...</div>
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
const stats = ref({});
const isLoading = ref(true);
const isLoadingStats = ref(true);
const error = ref('');
const message = ref('');

const newUser = ref({
  firstName: '',
  lastName: '',
  username: '',
  email: '',
  password: '',
  role: 'teacher'
});

const fetchStats = async () => {
  isLoadingStats.value = true;
  try {
    const response = await apiClient.get('/admin/system-stats');
    stats.value = response.data;
  } catch (err) {
    console.error('Failed to load system stats:', err);
  } finally {
    isLoadingStats.value = false;
  }
};

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
    Object.keys(newUser.value).forEach(key => newUser.value[key] = '');
    newUser.value.role = 'teacher';
    await fetchUsers();
    await fetchStats();
  } catch (err) {
    message.value = `Error: ${err.response?.data?.error || 'Could not create user.'}`;
  }
};

const deleteUser = async (userId) => {
  if (!confirm('Are you sure you want to delete this user? This action cannot be undone.')) return;
  message.value = '';
  try {
    const response = await apiClient.delete(`/admin/users/${userId}`);
    message.value = response.data.message;
    await fetchUsers();
    await fetchStats();
  } catch (err) {
    message.value = `Error: ${err.response?.data?.error || 'Could not delete user.'}`;
  }
};

onMounted(() => {
  fetchStats();
  fetchUsers();
});
</script>

<style scoped>
.admin-container { max-width: 1100px; margin: 2rem auto; padding: 2rem; }

/* Analytics Section */
.analytics-section { background: white; padding: 2rem; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); margin-bottom: 2.5rem; }
.analytics-section h2 { margin-top: 0; margin-bottom: 1.5rem; }
.stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1.5rem; margin-bottom: 1.5rem; }
.stat-card { background: #f8f9fa; padding: 1.5rem; border-radius: 8px; text-align: center; border: 1px solid #e9ecef; }
.stat-value { font-size: 2.2rem; font-weight: bold; color: #007bff; }
.stat-label { color: #6c757d; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 1px; margin-top: 0.25rem; }
.stat-breakdown { font-size: 0.8rem; color: #868e96; margin-top: 0.5rem; }
.text-success { color: #28a745 !important; }
.text-danger { color: #dc3545 !important; }

.top-courses { margin-top: 1rem; }
.top-courses h3 { margin-bottom: 0.75rem; font-size: 1rem; color: #495057; }
.top-courses-list { display: flex; flex-direction: column; gap: 0.5rem; }
.top-course-item { display: flex; align-items: center; gap: 1rem; padding: 0.75rem; background: #f8f9fa; border-radius: 6px; }
.top-rank { font-weight: bold; color: #007bff; font-size: 1.1rem; width: 30px; }
.top-title { flex: 1; font-weight: 500; }
.top-enrollments { color: #6c757d; font-size: 0.85rem; }

/* Form */
.form-card { background: #fff; padding: 2rem; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); margin-bottom: 2rem; }
.form-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 1.5rem; margin-bottom: 1.5rem; }
.form-group label { display: block; margin-bottom: 0.5rem; font-weight: 500; }
.form-group input, .form-group select { width: 100%; padding: 0.75rem; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; }
.btn-create { background-color: #007bff; color: white; padding: 0.75rem 1.5rem; border: none; border-radius: 4px; cursor: pointer; font-weight: bold; }

/* Table */
.user-table { width: 100%; border-collapse: collapse; margin-top: 1rem; }
.user-table th, .user-table td { border: 1px solid #ddd; padding: 0.8rem; text-align: left; }
.user-table th { background-color: #f8f9fa; }
.btn-delete { background-color: #dc3545; color: white; padding: 0.4rem 0.8rem; border: none; border-radius: 4px; cursor: pointer; }

.error-message, .success-message { padding: 1rem; border-radius: 4px; margin-bottom: 1rem; }
.error-message { background-color: #f8d7da; color: #721c24; }
.success-message { background-color: #d4edda; color: #155724; }
.loading { color: #6c757d; padding: 1rem; }
</style>