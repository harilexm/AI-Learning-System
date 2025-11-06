<template>
  <div class="dashboard-container">
    
    <!-- NEW: Recommendations Section -->
    <div class="recommendations-section">
      <h2>Recommended for You</h2>
      <div v-if="isLoadingRecs" class="loading">Generating recommendations...</div>
      <div v-else-if="recommendations.length > 0" class="recommendations-grid">
        <div v-for="rec in recommendations" :key="rec.id" class="rec-card">
          <span class="rec-icon">{{ getIconFor(rec.type) }}</span>
          <div class="rec-info">
            <span class="rec-title">{{ rec.title }}</span>
            <span class="rec-context">{{ rec.course_title }} / {{ rec.module_title }}</span>
          </div>
          <RouterLink :to="{ name: 'course-details', params: { courseId: rec.course_id } }" class="btn-rec">
            Go &rarr;
          </RouterLink>
        </div>
      </div>
      <p v-else class="loading">Complete more tagged content to get new recommendations!</p>
    </div>

    <hr class="divider" />

    <!-- Existing Course Library -->
    <h1>Course Library</h1>
    <p>Browse our available courses and start your learning journey.</p>
    
    <div v-if="isLoadingCourses" class="loading">Loading courses...</div>
    <div v-else-if="error" class="error-message">{{ error }}</div>
    
    <div v-else class="course-grid">
      <div v-for="course in courses" :key="course.id" class="course-card">
        <h3>{{ course.title }}</h3>
        <p class="course-author">Created by: {{ course.author }}</p>
        <p class="course-desc">{{ course.description }}</p>
        <RouterLink :to="{ name: 'course-details', params: { courseId: course.id } }" class="btn">
          View Course
        </RouterLink>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { RouterLink } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import axios from 'axios';

const authStore = useAuthStore();
const courses = ref([]);
const recommendations = ref([]); // New state for recommendations
const isLoadingCourses = ref(true);
const isLoadingRecs = ref(true); // New loading state
const error = ref('');

const apiClient = axios.create({
  baseURL: 'http://localhost:5000/api',
  headers: { Authorization: `Bearer ${authStore.token}` }
});

const fetchCourses = async () => {
  isLoadingCourses.value = true;
  try {
    const response = await apiClient.get('/courses');
    courses.value = response.data;
  } catch (err) {
    error.value = 'Failed to load courses.';
  } finally {
    isLoadingCourses.value = false;
  }
};

const fetchRecommendations = async () => {
  isLoadingRecs.value = true;
  try {
    const response = await apiClient.get('/students/me/recommendations');
    recommendations.value = response.data;
  } catch (err) {
    // Fail silently, it's not a critical error if recs don't load
    console.error("Could not load recommendations:", err);
  } finally {
    isLoadingRecs.value = false;
  }
};

// Helper for icons in recommendations
const getIconFor = (type) => {
  if (type === 'video') return '▶️';
  if (type === 'article') return '📄';
  if (type === 'quiz') return '❓';
  return '🔗';
};

onMounted(() => {
  // Fetch both courses and recommendations when the page loads
  fetchCourses();
  fetchRecommendations();
});
</script>

<style scoped>
/* --- NEW STYLES --- */
.recommendations-section {
  background: #f8f9fa;
  padding: 2rem;
  border-radius: 8px;
  margin-bottom: 2rem;
}
.recommendations-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1rem;
}
.rec-card {
  background: #fff;
  border: 1px solid #dee2e6;
  border-radius: 5px;
  padding: 1rem;
  display: flex;
  align-items: center;
  gap: 1rem;
}
.rec-icon { font-size: 1.5rem; }
.rec-info { flex-grow: 1; }
.rec-title { font-weight: bold; display: block; }
.rec-context { font-size: 0.85rem; color: #6c757d; }
.btn-rec {
  background-color: #6c757d;
  color: white;
  padding: 0.5rem 1rem;
  border-radius: 5px;
  text-decoration: none;
  white-space: nowrap;
}
.divider {
  border: none;
  border-top: 1px solid #e9ecef;
  margin: 2rem 0;
}

/* --- EXISTING STYLES (UNCHANGED) --- */
.dashboard-container { max-width: 1200px; margin: 2rem auto; padding: 1rem; }
.course-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 1.5rem; margin-top: 2rem; }
.course-card { background: #fff; border: 1px solid #e9ecef; border-radius: 8px; padding: 1.5rem; box-shadow: 0 2px 4px rgba(0,0,0,0.05); display: flex; flex-direction: column; }
.course-card h3 { margin-top: 0; }
.course-author { font-style: italic; color: #6c757d; font-size: 0.9rem; }
.course-desc { flex-grow: 1; color: #495057; line-height: 1.5; }
.btn { display: block; text-align: center; margin-top: 1rem; background-color: #28a745; color: white; padding: 0.75rem; border-radius: 5px; text-decoration: none; font-weight: bold; }
.error-message { color: #dc3545; }
.loading { color: #6c757d; }
</style>