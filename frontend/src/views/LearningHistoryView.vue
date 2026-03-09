<template>
  <div class="history-container">
    <h1>My Progress</h1>
    <p>Track your learning journey across all enrolled courses.</p>

    <div v-if="isLoading" class="loading">Loading your progress...</div>
    <div v-else-if="error" class="error-message">{{ error }}</div>

    <div v-else>
      <!-- Overall Stats -->
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-value">{{ history.courses_enrolled }}</div>
          <div class="stat-label">Courses Enrolled</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ history.content_completed }}</div>
          <div class="stat-label">Items Completed</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ history.quizzes_taken }}</div>
          <div class="stat-label">Quizzes Taken</div>
        </div>
        <div class="stat-card">
          <div class="stat-value" :class="{'text-success': history.avg_score >= 70, 'text-danger': history.avg_score < 70}">
            {{ history.avg_score }}%
          </div>
          <div class="stat-label">Overall Avg Score</div>
        </div>
      </div>

      <!-- Course Progress -->
      <div class="section-card">
        <h2>Course Progress</h2>
        <div v-if="history.course_progress.length === 0" class="empty-state">You haven't enrolled in any courses yet.</div>
        <div v-else class="progress-list">
          <div v-for="cp in history.course_progress" :key="cp.course_id" class="progress-item">
            <div class="progress-header">
              <span class="course-name">{{ cp.course_title }}</span>
              <span class="progress-pct">{{ cp.percentage }}%</span>
            </div>
            <div class="progress-bar-track">
              <div class="progress-bar-fill" :style="{ width: cp.percentage + '%' }" :class="getBarClass(cp.percentage)"></div>
            </div>
            <p class="progress-detail">{{ cp.completed_items }} / {{ cp.total_items }} items completed</p>
          </div>
        </div>
      </div>

      <!-- Quiz History -->
      <div class="section-card">
        <h2>Quiz History</h2>
        <div v-if="history.quiz_history.length === 0" class="empty-state">You haven't taken any quizzes yet.</div>
        <table v-else class="data-table">
          <thead>
            <tr>
              <th>Quiz</th>
              <th>Score</th>
              <th>Attempt</th>
              <th>Date</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(q, idx) in history.quiz_history" :key="idx">
              <td>{{ q.quiz_title }}</td>
              <td>
                <span :class="{'text-success': q.score >= 70, 'text-danger': q.score < 70}">{{ q.score }}%</span>
              </td>
              <td>{{ q.attempt_number }}</td>
              <td>{{ q.date }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import apiClient from '@/api';

const history = ref({
  courses_enrolled: 0,
  content_completed: 0,
  quizzes_taken: 0,
  avg_score: 0,
  course_progress: [],
  quiz_history: []
});
const isLoading = ref(true);
const error = ref('');

const getBarClass = (pct) => {
  if (pct >= 75) return 'bar-success';
  if (pct >= 40) return 'bar-warning';
  return 'bar-danger';
};

const fetchHistory = async () => {
  try {
    const response = await apiClient.get('/students/me/history');
    history.value = response.data;
  } catch (err) {
    error.value = err.response?.data?.error || 'Failed to load your progress.';
  } finally {
    isLoading.value = false;
  }
};

onMounted(fetchHistory);
</script>

<style scoped>
.history-container { max-width: 900px; margin: 2rem auto; padding: 1rem; }
.stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 1.5rem; margin-bottom: 2rem; }
.stat-card { background: white; padding: 1.5rem; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); text-align: center; }
.stat-value { font-size: 2.2rem; font-weight: bold; color: #007bff; }
.stat-label { color: #6c757d; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 1px; margin-top: 0.25rem; }
.text-success { color: #28a745 !important; }
.text-danger { color: #dc3545 !important; }

.section-card { background: white; padding: 1.5rem; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); margin-bottom: 1.5rem; }
.section-card h2 { margin-top: 0; margin-bottom: 1rem; font-size: 1.2rem; }

.progress-item { margin-bottom: 1.25rem; }
.progress-header { display: flex; justify-content: space-between; margin-bottom: 0.25rem; }
.course-name { font-weight: 600; }
.progress-pct { font-weight: bold; color: #495057; }
.progress-bar-track { background: #e9ecef; border-radius: 8px; height: 10px; overflow: hidden; }
.progress-bar-fill { height: 100%; border-radius: 8px; transition: width 0.5s ease; }
.bar-success { background: linear-gradient(90deg, #28a745, #20c997); }
.bar-warning { background: linear-gradient(90deg, #ffc107, #fd7e14); }
.bar-danger { background: linear-gradient(90deg, #dc3545, #e83e8c); }
.progress-detail { font-size: 0.8rem; color: #6c757d; margin-top: 0.25rem; }

.data-table { width: 100%; border-collapse: collapse; }
.data-table th, .data-table td { padding: 0.75rem; text-align: left; border-bottom: 1px solid #eee; }
.data-table th { color: #6c757d; font-size: 0.85rem; text-transform: uppercase; }

.empty-state { color: #6c757d; font-style: italic; }
.loading { text-align: center; padding: 3rem; font-size: 1.1rem; color: #6c757d; }
.error-message { color: #dc3545; text-align: center; }
</style>
