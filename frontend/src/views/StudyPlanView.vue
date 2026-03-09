<template>
  <div class="study-plan-container">
    <div class="header-actions">
      <RouterLink :to="{ name: 'course-details', params: { courseId } }" class="btn-back">
        &larr; Back to Course
      </RouterLink>
    </div>

    <h1>Your Personalized Study Plan</h1>
    <p>This plan was AI-generated based on your learning profile and recent quiz performance.</p>

    <div v-if="isLoading" class="loading">
      <div class="spinner"></div> Generating your custom pathway... (This may take up to 20 seconds)
    </div>
    <div v-else-if="error" class="error-message">
      {{ error }}
    </div>
    
    <div v-else-if="planData" class="plan-content">
      <div v-for="day in planData.days" :key="day.day" class="day-card">
        <h3>Day {{ day.day }}: {{ day.focus }}</h3>
        <p class="duration">⏱️ {{ day.duration_minutes }} minutes</p>
        <ul class="activity-list">
          <li v-for="(activity, idx) in day.activities" :key="idx">
            {{ activity }}
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import apiClient from '@/api';

const route = useRoute();
const courseId = route.params.courseId;

const planData = ref(null);
const isLoading = ref(true);
const error = ref('');

const fetchOrGeneratePlan = async () => {
    isLoading.value = true;
    error.value = '';
    try {
        const response = await apiClient.post('/study-plan', { course_id: courseId });
        planData.value = response.data;
    } catch (err) {
        error.value = err.response?.data?.error || "Failed to generate study plan. Please try again.";
    } finally {
        isLoading.value = false;
    }
};

onMounted(() => {
    fetchOrGeneratePlan();
});
</script>

<style scoped>
.study-plan-container { max-width: 800px; margin: 2rem auto; padding: 1rem; }
.header-actions { margin-bottom: 2rem; }
.btn-back { display: inline-block; padding: 0.5rem 1rem; background-color: #6c757d; color: white; border-radius: 4px; text-decoration: none; font-weight: bold; }
.plan-content { margin-top: 2rem; display: flex; flex-direction: column; gap: 1.5rem; }
.day-card { background: white; border: 1px solid #e9ecef; border-left: 5px solid #007bff; border-radius: 8px; padding: 1.5rem; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
.day-card h3 { margin-top: 0; color: #343a40; font-size: 1.25rem; }
.duration { font-weight: bold; color: #28a745; margin-bottom: 1rem; }
.activity-list { padding-left: 1.5rem; color: #495057; }
.activity-list li { margin-bottom: 0.5rem; }
.loading { text-align: center; padding: 3rem; font-size: 1.2rem; color: #007bff; }
.spinner { display: inline-block; width: 2rem; height: 2rem; border: 3px solid rgba(0,123,255,0.3); border-radius: 50%; border-top-color: #007bff; animation: spin 1s ease-in-out infinite; margin-right: 0.5rem; vertical-align: middle; }
@keyframes spin { to { transform: rotate(360deg); } }
.error-message { padding: 1rem; background: #f8d7da; color: #721c24; border-radius: 8px; text-align: center; }
</style>
