<script setup>
import { RouterLink, RouterView } from 'vue-router'
import { useAuthStore } from './stores/auth';
import { useRouter } from 'vue-router';

const authStore = useAuthStore();
const router = useRouter();

const handleLogout = () => {
  authStore.logout();
  router.push('/login');
};
</script>

<template>
  <div id="app-container">
    <header class="app-header">
      <nav class="main-nav">
        
        <RouterLink to="/">Home</RouterLink>
        <RouterLink to="/about">About</RouterLink>
        
        
        <div class="nav-spacer"></div>

      
        <template v-if="!authStore.isAuthenticated">
          <RouterLink to="/login">Login</RouterLink>
          <RouterLink to="/register">Register</RouterLink>
        </template>
        
        
        <template v-if="authStore.isAuthenticated">
          <RouterLink to="/profile">My Profile</RouterLink>
          <RouterLink to="/dashboard">Dashboard</RouterLink>

          <RouterLink v-if="authStore.isTeacher || authStore.isAdmin" to="/manage-courses">
          Manage Courses
          </RouterLink>
          <a @click="handleLogout" href="#" class="logout-link">Logout</a>
        </template>
      </nav>
    </header>

    <main class="main-content">
      <RouterView />
    </main>
  </div>
</template>

<style scoped>
#app-container {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.app-header {
  width: 100%;
  background-color: #fff;
  border-bottom: 1px solid #e2e8f0;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
  padding: 0 2rem;
}

.main-nav {
  display: flex;
  align-items: center;
  max-width: 1280px;
  margin: 0 auto;
  height: 60px;
  font-size: 1rem;
}

.main-nav a {
  padding: 0 1rem;
  color: #2c3e50;
  text-decoration: none;
  font-weight: 500;
  transition: color 0.3s;
}

.main-nav a:hover {
  color: hsla(160, 100%, 37%, 1);
  background-color: transparent; 
}

.main-nav a.router-link-exact-active {
  color: hsla(160, 100%, 37%, 1);
  border-bottom: 2px solid hsla(160, 100%, 37%, 1);
}

.nav-spacer {
  flex-grow: 1;
}

.logout-link {
  cursor: pointer;
}

.main-content {
  flex-grow: 1;
  width: 100%;
  max-width: 1280px;
  margin: 0 auto;
  padding: 2rem;
}
</style>