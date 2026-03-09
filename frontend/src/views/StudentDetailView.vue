<template>
  <div class="student-detail-container">
    <div class="header-actions">
      <RouterLink to="/teacher-dashboard" class="btn-back">&larr; Back to Dashboard</RouterLink>
    </div>

    <div v-if="isLoading" class="loading">Loading student details...</div>
    <div v-else-if="error" class="error-message">{{ error }}</div>

    <div v-else-if="student">
      <!-- Student Profile Card -->
      <div class="profile-card">
        <div class="profile-avatar">{{ student.name.charAt(0) }}</div>
        <div class="profile-info">
          <h1>{{ student.name }}</h1>
          <p class="email">{{ student.email }}</p>
          <p class="meta">Joined: {{ student.joined }} | Avg Score: 
            <span :class="{'text-success': student.overall_avg_score >= 70, 'text-danger': student.overall_avg_score < 70}">
              {{ student.overall_avg_score }}%
            </span> 
            | Quizzes Taken: {{ student.total_quizzes }}
          </p>
          <div v-if="student.learning_profile" class="profile-tags">
            <span class="tag">Style: {{ student.learning_profile.learning_style || 'Not set' }}</span>
            <span class="tag">Pace: {{ student.learning_profile.preferred_pace || 'Medium' }}</span>
            <span class="tag" v-if="student.learning_profile.primary_goal">Goal: {{ student.learning_profile.primary_goal }}</span>
          </div>
        </div>
      </div>

      <!-- Course Progress -->
      <div class="section-card">
        <h2>Course Progress</h2>
        <div v-if="student.course_progress.length === 0" class="empty-state">Not enrolled in any courses yet.</div>
        <div v-else class="progress-list">
          <div v-for="cp in student.course_progress" :key="cp.course_id" class="progress-item">
            <div class="progress-header">
              <span class="course-name">{{ cp.course_title }}</span>
              <span class="progress-pct">{{ cp.percentage }}%</span>
            </div>
            <div class="progress-bar-track">
              <div class="progress-bar-fill" :style="{ width: cp.percentage + '%' }" :class="getProgressClass(cp.percentage)"></div>
            </div>
            <p class="progress-detail">{{ cp.completed_items }} / {{ cp.total_items }} items completed</p>
          </div>
        </div>
      </div>

      <!-- Quiz History -->
      <div class="section-card">
        <h2>Quiz History</h2>
        <div v-if="student.quiz_history.length === 0" class="empty-state">No quizzes attempted yet.</div>
        <table v-else class="data-table">
          <thead>
            <tr>
              <th>Quiz</th>
              <th>Score</th>
              <th>Attempt #</th>
              <th>Date</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(q, idx) in student.quiz_history" :key="idx">
              <td>{{ q.quiz_title }}</td>
              <td>
                <span :class="{'text-success': q.score >= 70, 'text-danger': q.score < 70}">
                  {{ q.score }}%
                </span>
              </td>
              <td>{{ q.attempt_number }}</td>
              <td>{{ q.date }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Teacher Remarks Section (placeholder for Phase 6B) -->
      <div class="section-card remarks-section">
        <h2>Teacher Remarks</h2>
        <div class="remark-form">
          <select v-model="newRemark.type" class="remark-type-select">
            <option value="remark">Remark</option>
            <option value="encouragement">Encouragement</option>
            <option value="warning">Warning</option>
          </select>
          <textarea v-model="newRemark.message" placeholder="Write a remark for this student..." rows="3"></textarea>
          <button @click="sendRemark" class="btn btn-primary" :disabled="!newRemark.message.trim()">
            Send Remark
          </button>
        </div>
        <div v-if="remarks.length > 0" class="remarks-list">
          <div v-for="r in remarks" :key="r.id" class="remark-item" :class="'remark-' + r.type">
            <div class="remark-header">
              <span class="remark-type-badge">{{ r.type }}</span>
              <span class="remark-date">{{ r.created_at }}</span>
            </div>
            <p class="remark-text">{{ r.message }}</p>
          </div>
        </div>
        <p v-else class="empty-state">No remarks sent yet.</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRoute, RouterLink } from 'vue-router';
import apiClient from '@/api';

const route = useRoute();
const studentId = route.params.studentId;

const student = ref(null);
const remarks = ref([]);
const isLoading = ref(true);
const error = ref('');
const newRemark = ref({ type: 'remark', message: '' });

const fetchStudent = async () => {
  try {
    const response = await apiClient.get(`/teacher/students/${studentId}`);
    student.value = response.data;
  } catch (err) {
    error.value = err.response?.data?.error || 'Failed to load student details.';
  } finally {
    isLoading.value = false;
  }
};

const fetchRemarks = async () => {
  try {
    const response = await apiClient.get(`/teacher/students/${studentId}/remarks`);
    remarks.value = response.data;
  } catch (err) {
    // Remarks API will be built in Phase 6B, silently fail for now
    console.log('Remarks API not available yet');
  }
};

const sendRemark = async () => {
  if (!newRemark.value.message.trim()) return;
  try {
    await apiClient.post(`/teacher/students/${studentId}/remarks`, newRemark.value);
    newRemark.value.message = '';
    await fetchRemarks();
  } catch (err) {
    alert(err.response?.data?.error || 'Failed to send remark.');
  }
};

const getProgressClass = (pct) => {
  if (pct >= 75) return 'bar-success';
  if (pct >= 40) return 'bar-warning';
  return 'bar-danger';
};

onMounted(() => {
  fetchStudent();
  fetchRemarks();
});
</script>

<style scoped>
.student-detail-container { max-width: 900px; margin: 2rem auto; padding: 1rem; }
.header-actions { margin-bottom: 1.5rem; }
.btn-back { display: inline-block; padding: 0.5rem 1rem; background-color: #6c757d; color: white; border-radius: 4px; text-decoration: none; font-weight: bold; }

/* Profile Card */
.profile-card { display: flex; align-items: center; gap: 1.5rem; background: white; padding: 2rem; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); margin-bottom: 2rem; }
.profile-avatar { width: 80px; height: 80px; border-radius: 50%; background: linear-gradient(135deg, #667eea, #764ba2); color: white; display: flex; align-items: center; justify-content: center; font-size: 2rem; font-weight: bold; flex-shrink: 0; }
.profile-info h1 { margin: 0 0 0.25rem 0; font-size: 1.5rem; }
.email { color: #6c757d; margin: 0 0 0.5rem 0; }
.meta { font-size: 0.9rem; color: #495057; margin: 0; }
.profile-tags { display: flex; gap: 0.5rem; margin-top: 0.75rem; flex-wrap: wrap; }
.tag { background: #e9ecef; padding: 0.25rem 0.75rem; border-radius: 12px; font-size: 0.8rem; color: #495057; }

/* Section Card */
.section-card { background: white; padding: 1.5rem; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); margin-bottom: 1.5rem; }
.section-card h2 { margin-top: 0; margin-bottom: 1rem; font-size: 1.2rem; color: #343a40; }

/* Progress Bars */
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

/* Data Table */
.data-table { width: 100%; border-collapse: collapse; }
.data-table th, .data-table td { padding: 0.75rem; text-align: left; border-bottom: 1px solid #eee; }
.data-table th { color: #6c757d; font-size: 0.85rem; text-transform: uppercase; }
.text-success { color: #28a745; font-weight: bold; }
.text-danger { color: #dc3545; font-weight: bold; }

/* Remarks */
.remarks-section { border-left: 4px solid #007bff; }
.remark-form { display: flex; flex-direction: column; gap: 0.75rem; margin-bottom: 1.5rem; }
.remark-form textarea { width: 100%; padding: 0.75rem; border: 1px solid #ccc; border-radius: 4px; resize: vertical; box-sizing: border-box; }
.remark-type-select { padding: 0.5rem; border: 1px solid #ccc; border-radius: 4px; width: fit-content; }
.btn { padding: 0.75rem 1.5rem; border: none; border-radius: 4px; cursor: pointer; font-weight: bold; }
.btn:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-primary { background-color: #007bff; color: white; width: fit-content; }
.remarks-list { display: flex; flex-direction: column; gap: 0.75rem; }
.remark-item { padding: 1rem; border-radius: 6px; border: 1px solid #e9ecef; }
.remark-remark { border-left: 3px solid #007bff; }
.remark-encouragement { border-left: 3px solid #28a745; background: #f0fff4; }
.remark-warning { border-left: 3px solid #dc3545; background: #fff5f5; }
.remark-header { display: flex; justify-content: space-between; margin-bottom: 0.5rem; }
.remark-type-badge { text-transform: uppercase; font-size: 0.75rem; font-weight: bold; padding: 0.15rem 0.5rem; border-radius: 4px; background: #e9ecef; }
.remark-date { font-size: 0.8rem; color: #6c757d; }
.remark-text { margin: 0; color: #333; }

.empty-state { color: #6c757d; font-style: italic; }
.loading { text-align: center; padding: 3rem; font-size: 1.1rem; color: #6c757d; }
.error-message { color: #dc3545; text-align: center; padding: 2rem; }
</style>
