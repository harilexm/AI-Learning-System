<template>
  <div class="home-container">
    <header class="hero-section">
      <!-- Show a different heading if the user is logged in -->
      <h1 v-if="authStore.isAuthenticated">Welcome Back!</h1>
      <h1 v-else>Welcome to the Future of Learning</h1>

      <p class="subtitle">
        An AI-Powered Personalized Learning System designed to adapt to your unique learning style.
      </p>

      <!-- show different buttons based on the login state -->
      <div class="cta-buttons">
        <!-- Show these buttons ONLY if the user is NOT authenticated -->
        <template v-if="!authStore.isAuthenticated">
          <RouterLink to="/login" class="btn btn-primary">Log In</RouterLink>
          <RouterLink to="/register" class="btn btn-secondary">Get Started</RouterLink>
        </template>
        <!-- Show this button ONLY if the user IS authenticated -->
        <template v-else>
          <RouterLink to="/dashboard" class="btn btn-primary">Go to Dashboard</RouterLink>
        </template>
      </div>
    </header>

    <section class="features-section">
      <h2>Why Choose Our Platform?</h2>
      <div class="features-grid">
        <div class="feature-card">
          <h3>Personalized Paths</h3>
          <p>Our AI analyzes your performance to create a custom learning journey just for you.</p>
        </div>
        <div class="feature-card">
          <h3>Interactive Content</h3>
          <p>Engage with dynamic quizzes, videos, and articles that make learning fun.</p>
        </div>
        <div class="feature-card">
          <h3>Track Your Progress</h3>
          <p>Visualize your growth and see your achievements with our detailed analytics.</p>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { RouterLink } from 'vue-router';
import { useAuthStore } from '@/stores/auth';

const authStore = useAuthStore();
</script>

<style scoped>
.home-container {max-width: 1200px; margin: 0 auto; padding: 2rem; color: #333;}
.hero-section {text-align: center; padding: 4rem 1rem; background-color: #f8f9fa; border-radius: 8px; margin-bottom: 3rem;}
h1 {font-size: 2.5rem; font-weight: bold; margin-bottom: 1rem; color: #2c3e50;}
.subtitle { font-size: 1.2rem; color: #6c757d; max-width: 600px;margin: 0 auto 2rem auto;}
.cta-buttons { display: flex; justify-content: center; gap: 1rem;}
.btn {padding: 0.75rem 1.5rem; border-radius: 5px; text-decoration: none; font-weight: bold; transition: all 0.3s ease;}
.btn-primary { background-color: #007bff; color: white;}
.btn-primary:hover { background-color: #0056b3;}
.btn-secondary { background-color: transparent; color: #007bff; border: 2px solid #007bff;}
.btn-secondary:hover { background-color: #007bff; color: white;}
.features-section { text-align: center;}
.features-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 2rem; margin-top: 2rem;}
.feature-card { padding: 2rem; border: 1px solid #e9ecef; border-radius: 8px; background-color: #fff; box-shadow: 0 2px 4px rgba(0,0,0,0.05);}
.feature-card h3 { margin-top: 0; color: #007bff;}
</style>