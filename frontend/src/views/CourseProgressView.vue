<template>
  <div class="progress-container">
    <div v-if="isLoading" class="loading">Loading Analytics Data...</div>
    <div v-else-if="error" class="error-message">{{ error }}</div>
    
    <div v-else>
      <h1>Analytics for "{{ courseTitle }}"</h1>
      
      <!-- View Toggle Buttons -->
      <div class="view-toggle">
        <button @click="currentView = 'completion'" :class="{ active: currentView === 'completion' }">
          Completion Progress
        </button>
        <button @click="currentView = 'performance'" :class="{ active: currentView === 'performance' }">
          Quiz Performance
        </button>
      </div>

      <!-- Completion Progress View -->
      <div v-if="currentView === 'completion'">
        <div v-if="progressData.length === 0" class="no-data">
          <p>No students have started this course yet.</p>
        </div>
        <table v-else class="progress-table">
          <thead>
            <tr>
              <th>Student Name</th>
              <th>Progress</th>
              <th>Summary</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="student in progressData" :key="student.student_id">
              <td>{{ student.student_name }}</td>
              <td>
                <div class="progress-bar-container">
                  <div class="progress-bar" :style="{ width: student.percentage + '%' }"></div>
                </div>
              </td>
              <td>{{ student.completed_count }} / {{ student.total_items }} items ({{ student.percentage }}%)</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Quiz Performance View -->
      <div v-if="currentView === 'performance'">
        <div v-if="performanceData.length === 0" class="no-data">
            <p>No students have taken any quizzes in this course yet.</p>
        </div>
        <div v-else class="performance-grid">
            <div v-for="student in performanceData" :key="student.student_id" class="student-card">
                <h3>{{ student.student_name }}</h3>
                <p class="average-score">Average Score: <strong>{{ student.average_score }}%</strong></p>
                <ul class="attempt-list">
                    <li v-for="attempt in student.attempts" :key="`${attempt.quiz_id}-${attempt.attempt_number}`">
                        <span>{{ attempt.quiz_title }} (Attempt #{{ attempt.attempt_number }})</span>
                        <strong class="score">{{ attempt.score }}%</strong>
                    </li>
                </ul>
            </div>
        </div>
      </div>
    </div>
    <RouterLink to="/manage-courses" class="btn-back">&larr; Back to Course Management</RouterLink>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRoute, RouterLink } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import apiClient from '@/api';

const route = useRoute();
const authStore = useAuthStore();
const courseTitle = ref('');
const isLoading = ref(true);
const error = ref('');

const currentView = ref('completion');
const progressData = ref([]);
const performanceData = ref([]); // state to hold the quiz performance data



// ENHANCED DATA FETCHING
const fetchAnalyticsData = async () => {
  const courseId = route.params.courseId;
  isLoading.value = true;
  try {
    // Fetch all required data in parallel for better performance
    const [progressResponse, performanceResponse, courseResponse] = await Promise.all([
        apiClient.get(`/courses/${courseId}/progress`),
        apiClient.get(`/courses/${courseId}/performance`), // New API call
        apiClient.get(`/courses/${courseId}`)
    ]);
    
    progressData.value = progressResponse.data;
    performanceData.value = performanceResponse.data; // Store the new data
    courseTitle.value = courseResponse.data.title;

  } catch (err) {
    error.value = 'Failed to load analytics data. Please try again.';
    console.error(err); // Log the actual error for debugging
  } finally {
    isLoading.value = false;
  }
};

onMounted(fetchAnalyticsData);
</script>

<style scoped>
.progress-container { max-width: 1000px; margin: 2rem auto; padding: 2rem; background: #fff; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
.progress-table { width: 100%; border-collapse: collapse; margin-top: 2rem; }
.progress-table th, .progress-table td { border: 1px solid #ddd; padding: 1rem; text-align: left; }
.progress-table th { background-color: #f8f9fa; }
.progress-bar-container { width: 100%; background-color: #e9ecef; border-radius: 5px; height: 20px; }
.progress-bar { background-color: #28a745; height: 100%; border-radius: 5px; transition: width 0.5s ease-in-out; }
.no-data, .loading, .error-message { text-align: center; padding: 3rem; font-size: 1.2rem; color: #6c757d; }
.btn-back { display: inline-block; margin-top: 2rem; text-decoration: none; color: #007bff; font-weight: bold; }
.view-toggle {display: flex; gap: 0.5rem; margin-bottom: 2rem; border-bottom: 1px solid #ddd; padding-bottom: 1rem;}
.view-toggle button { padding: 0.5rem 1rem; border: 1px solid #ccc; background-color: #f8f9fa; cursor: pointer; border-radius: 5px; font-weight: 500; transition: all 0.2s ease-in-out; }
.view-toggle button.active { background-color: #007bff; color: white; border-color: #007bff; }
.performance-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 1.5rem; margin-top: 2rem; }
.student-card { border: 1px solid #e9ecef; border-radius: 8px; padding: 1.5rem;}
.student-card h3 { margin-top: 0; border-bottom: 1px solid #eee; padding-bottom: 0.5rem; margin-bottom: 1rem; }
.average-score { font-size: 1.1rem; color: #343a40; }
.average-score strong { font-size: 1.3rem; color: #007bff; }
.attempt-list { list-style: none; padding: 0; margin-top: 1rem; }
.attempt-list li { display: flex; justify-content: space-between; align-items: center; padding: 0.5rem 0; border-bottom: 1px solid #f1f1f1; font-size: 0.95rem;}
.attempt-list li:last-child { border-bottom: none; }
.score {  font-weight: bold; font-size: 1rem; background-color: #e9ecef; padding: 0.2rem 0.5rem; border-radius: 4px;}
</style>