<template>
  <div class="dashboard-container">

    <!-- Teacher Feedback Section -->
    <div v-if="authStore.isStudent && remarks.length > 0" class="feedback-section">
      <h2>Teacher Feedback</h2>
      <div class="remarks-list">
        <div v-for="r in remarks" :key="r.id" class="remark-item" :class="'remark-' + r.type">
          <div class="remark-header">
            <span class="remark-type-badge" :class="'badge-' + r.type">{{ r.type }}</span>
            <span class="remark-meta">{{ r.teacher_name }} &mdash; {{ r.created_at }}</span>
          </div>
          <p class="remark-text">{{ r.message }}</p>
        </div>
      </div>
    </div>

    <!-- Recommendations Section -->
    <div v-if="authStore.isStudent" class="recommendations-section">
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
    <hr v-if="authStore.isStudent" class="divider" />

    <!-- My Learning Section -->
    <div v-if="authStore.isStudent && enrolledCourses.length > 0" class="my-learning-section">
      <h2>My Learning</h2>
      <div class="course-grid">
        <div v-for="enr in enrolledCourses" :key="enr.course_id" class="course-card enrolled-card">
          <h3>{{ enr.title }}</h3>
          <p class="course-desc">{{ enr.description }}</p>
          <div class="card-actions">
            <RouterLink :to="{ name: 'course-details', params: { courseId: enr.course_id } }" class="btn btn-primary">
              Continue Learning
            </RouterLink>
            <button @click="unenroll(enr.course_id)" class="btn btn-danger">Unenroll</button>
          </div>
        </div>
      </div>
      <hr class="divider" />
    </div>

    <!-- Existing Course Library -->
    <h1>Course Library</h1>
    <p>Browse our available courses and start your learning journey.</p>
    
    <div v-if="isLoadingCourses" class="loading">Loading courses...</div>
    <div v-else-if="error" class="error-message">{{ error }}</div>
    
    <div v-else class="course-grid">
      <div v-for="course in availableCourses" :key="course.id" class="course-card">
        <h3>{{ course.title }}</h3>
        <p class="course-author">Created by: {{ course.author }}</p>
        <p class="course-desc">{{ course.description }}</p>
        <div class="card-actions" v-if="authStore.isStudent">
            <button @click="enroll(course.id)" class="btn btn-success" :disabled="isEnrolling === course.id">
              {{ isEnrolling === course.id ? 'Enrolling...' : 'Enroll Now' }}
            </button>
        </div>
        <div class="card-actions" v-else>
            <RouterLink :to="{ name: 'course-details', params: { courseId: course.id } }" class="btn btn-primary">
              View Course
            </RouterLink>
        </div>
      </div>
      <p v-if="availableCourses.length === 0" class="muted">You are enrolled in all available courses!</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { RouterLink } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import apiClient from '@/api'; 

const authStore = useAuthStore();
const courses = ref([]);
const enrolledCourses = ref([]);
const availableCourses = ref([]);
const recommendations = ref([]);
const isLoadingCourses = ref(true);
const isLoadingRecs = ref(true);
const isEnrolling = ref(null);
const error = ref('');
const remarks = ref([]);

const fetchRemarks = async () => {
  try {
    const response = await apiClient.get('/students/me/remarks');
    remarks.value = response.data;
  } catch (err) {
    console.log('Could not load remarks');
  }
};

const fetchCourses = async () => {
  isLoadingCourses.value = true;
  try {
    const response = await apiClient.get('/courses');
    courses.value = response.data;
    
    if (authStore.isStudent) {
        const enrResponse = await apiClient.get('/students/me/enrollments');
        enrolledCourses.value = enrResponse.data;
        
        const enrolledIds = new Set(enrolledCourses.value.map(e => e.course_id));
        availableCourses.value = courses.value.filter(c => !enrolledIds.has(c.id));
    } else {
        availableCourses.value = courses.value;
    }
  } catch (err) {
    error.value = 'Failed to load courses.';
  } finally {
    isLoadingCourses.value = false;
  }
};

const enroll = async (courseId) => {
    isEnrolling.value = courseId;
    try {
        await apiClient.post(`/courses/${courseId}/enroll`);
        await fetchCourses(); // Refresh lists
    } catch (err) {
        alert(err.response?.data?.error || "Failed to enroll in course");
    } finally {
        isEnrolling.value = null;
    }
};

const unenroll = async (courseId) => {
    if(!confirm("Are you sure you want to drop this course?")) return;
    try {
        await apiClient.delete(`/courses/${courseId}/enroll`);
        await fetchCourses(); // Refresh lists
    } catch (err) {
        alert(err.response?.data?.error || "Failed to drop course");
    }
};

const fetchRecommendations = async () => {
  isLoadingRecs.value = true;
  try {
    const response = await apiClient.get('/students/me/recommendations');
    recommendations.value = response.data;
  } catch (err) {
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
  fetchCourses();
  if (authStore.isStudent) {
    fetchRecommendations();
    fetchRemarks();
  } else {
    isLoadingRecs.value = false;
  }
});
</script>

<style scoped>
/* Teacher Feedback */
.feedback-section { background: #fff3cd; padding: 1.5rem; border-radius: 8px; margin-bottom: 2rem; border-left: 4px solid #ffc107; }
.feedback-section h2 { margin-top: 0; margin-bottom: 1rem; font-size: 1.2rem; }
.remarks-list { display: flex; flex-direction: column; gap: 0.75rem; }
.remark-item { background: white; padding: 1rem; border-radius: 6px; border: 1px solid #e9ecef; }
.remark-remark { border-left: 3px solid #007bff; }
.remark-encouragement { border-left: 3px solid #28a745; background: #f0fff4; }
.remark-warning { border-left: 3px solid #dc3545; background: #fff5f5; }
.remark-header { display: flex; justify-content: space-between; margin-bottom: 0.5rem; flex-wrap: wrap; gap: 0.5rem; }
.remark-type-badge { text-transform: uppercase; font-size: 0.7rem; font-weight: bold; padding: 0.15rem 0.5rem; border-radius: 4px; }
.badge-remark { background: #cce5ff; color: #004085; }
.badge-encouragement { background: #d4edda; color: #155724; }
.badge-warning { background: #f8d7da; color: #721c24; }
.remark-meta { font-size: 0.8rem; color: #6c757d; }
.remark-text { margin: 0; color: #333; }

.recommendations-section {background: #f8f9fa; padding: 2rem; border-radius: 8px; margin-bottom: 2rem;}
.recommendations-grid { display: grid; grid-template-columns: 1fr; gap: 1rem;}
.rec-card {background: #fff; border: 1px solid #dee2e6; border-radius: 5px; padding: 1rem; display: flex; align-items: center;gap: 1rem;}
.rec-icon { font-size: 1.5rem; }
.rec-info { flex-grow: 1; }
.rec-title { font-weight: bold; display: block; }
.rec-context { font-size: 0.85rem; color: #6c757d; }
.btn-rec {background-color: #6c757d; color: white; padding: 0.5rem 1rem; border-radius: 5px; text-decoration: none; white-space: nowrap;}
.divider { border: none; border-top: 1px solid #e9ecef; margin: 2rem 0;}
.dashboard-container { max-width: 1200px; margin: 2rem auto; padding: 1rem; }
.course-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 1.5rem; margin-top: 2rem; }
.course-card { background: #fff; border: 1px solid #e9ecef; border-radius: 8px; padding: 1.5rem; box-shadow: 0 2px 4px rgba(0,0,0,0.05); display: flex; flex-direction: column; }
.course-card h3 { margin-top: 0; }
.course-author { font-style: italic; color: #6c757d; font-size: 0.9rem; }
.course-desc { flex-grow: 1; color: #495057; line-height: 1.5; }
.card-actions { display: flex; gap: 0.5rem; margin-top: 1rem; }
.btn { flex: 1; text-align: center; color: white; padding: 0.75rem; border-radius: 5px; text-decoration: none; font-weight: bold; border: none; cursor: pointer; }
.btn:disabled { opacity: 0.6; cursor: not-allowed; }
.btn-primary { background-color: #007bff; }
.btn-success { background-color: #28a745; }
.btn-danger { background-color: #dc3545; }
.enrolled-card { border-left: 4px solid #28a745; }
.muted { color: #6c757d; font-style: italic; }
.error-message { color: #dc3545; }
.loading { color: #6c757d; }
</style>