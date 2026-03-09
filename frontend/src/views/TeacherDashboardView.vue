<template>
  <div class="dashboard-container">
    <h1>Teacher Dashboard</h1>
    <p>Welcome! Here's an overview of your platform's learning activity.</p>
    
    <div v-if="isLoading" class="loading">Loading dashboard insights...</div>
    <div v-else-if="error" class="error-message">{{ error }}</div>
    
    <div v-else>
      <!-- Summary Cards -->
      <div class="summary-grid">
        <div class="summary-card">
          <div class="stat-value">{{ summary.total_students }}</div>
          <div class="stat-label">Total Students</div>
        </div>
        <div class="summary-card">
          <div class="stat-value">{{ summary.total_courses }}</div>
          <div class="stat-label">Active Courses</div>
        </div>
        <div class="summary-card">
          <div class="stat-value">{{ summary.total_quizzes_taken }}</div>
          <div class="stat-label">Quizzes Taken</div>
        </div>
        <div class="summary-card">
          <div class="stat-value" :class="{'text-success': summary.average_quiz_score >= 70, 'text-warning': summary.average_quiz_score < 70}">
            {{ summary.average_quiz_score }}%
          </div>
          <div class="stat-label">Avg Quiz Score</div>
        </div>
      </div>

      <div class="dashboard-widgets">
        <!-- At-Risk Students -->
        <div class="widget">
          <h2>At-Risk Students</h2>
          <p class="text-sm text-gray">Identified by ML learning gap analyzer</p>
          <ul v-if="summary.at_risk_students && summary.at_risk_students.length > 0" class="risk-list">
            <li v-for="student in summary.at_risk_students" :key="student.id">
              <div class="student-info">
                <RouterLink :to="{ name: 'student-detail', params: { studentId: student.id } }" class="student-name-link">
                  {{ student.name }}
                </RouterLink>
                <span class="student-email">{{ student.email }}</span>
              </div>
              <span class="risk-badge" :class="student.risk_level">{{ student.risk_level.replace('_', ' ') }}</span>
            </li>
          </ul>
          <p v-else class="empty-state">No students are currently marked as at-risk. Great job!</p>
        </div>

        <!-- Recent Activity -->
        <div class="widget">
          <h2>Recent Activity</h2>
          <table class="activity-table" v-if="summary.recent_activity && summary.recent_activity.length > 0">
            <thead>
              <tr>
                <th>Student</th>
                <th>Quiz</th>
                <th>Score</th>
                <th>When</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(act, idx) in summary.recent_activity" :key="idx">
                <td>
                  <RouterLink :to="{ name: 'student-detail', params: { studentId: act.student_id } }" class="student-name-link">
                    {{ act.student_name }}
                  </RouterLink>
                  <span class="cell-email">{{ act.student_email }}</span>
                </td>
                <td>{{ act.quiz_title }}</td>
                <td>
                  <span :class="{'text-success': act.score >= 70, 'text-danger': act.score < 70}">
                    {{ act.score }}%
                  </span>
                </td>
                <td>{{ act.date }}</td>
              </tr>
            </tbody>
          </table>
          <p v-else class="empty-state">No recent activity found.</p>
        </div>
      </div>

      <!-- Student Queries (Discussion Posts) -->
      <div class="widget full-width-widget queries-widget">
        <div class="queries-header">
          <h2>Student Queries</h2>
          <span v-if="unansweredCount > 0" class="unanswered-counter">{{ unansweredCount }} unanswered</span>
        </div>
        <div v-if="isLoadingDiscussions" class="loading">Loading discussions...</div>
        <div v-else-if="discussions.length === 0" class="empty-state">No student discussions yet.</div>
        <div v-else class="queries-list">
          <div v-for="d in discussions" :key="d.id" class="query-item" :class="{ 'unanswered': !d.answered }">
            <div class="query-info">
              <div class="query-title-row">
                <span v-if="!d.answered" class="badge-unanswered">UNANSWERED</span>
                <span v-else class="badge-answered">ANSWERED</span>
                <span class="query-title">{{ d.title }}</span>
              </div>
              <p class="query-preview">{{ d.body }}</p>
              <div class="query-meta">
                <span class="query-author">{{ d.author }} ({{ d.author_role }})</span>
                <span class="query-course">{{ d.course_title }}</span>
                <span class="query-date">{{ d.created_at }}</span>
                <span class="query-replies">{{ d.reply_count }} {{ d.reply_count === 1 ? 'reply' : 'replies' }}</span>
              </div>
            </div>
            <RouterLink :to="{ name: 'course-discussions', params: { courseId: d.course_id } }" class="btn btn-sm btn-answer">
              View &rarr;
            </RouterLink>
          </div>
        </div>
      </div>

      <!-- All Students List -->
      <div class="widget full-width-widget">
        <div class="students-header">
          <h2>All Students</h2>
          <input v-model="searchQuery" type="text" placeholder="Search by name or email..." class="search-input" />
        </div>
        <div v-if="isLoadingStudents" class="loading">Loading students...</div>
        <table v-else-if="filteredStudents.length > 0" class="activity-table students-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Email</th>
              <th>Courses</th>
              <th>Quizzes</th>
              <th>Avg Score</th>
              <th>Completed</th>
              <th>Joined</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="s in filteredStudents" :key="s.id" @click="$router.push({ name: 'student-detail', params: { studentId: s.id } })" class="clickable-row">
              <td class="student-name-col">{{ s.name }}</td>
              <td>{{ s.email }}</td>
              <td>{{ s.enrollment_count }}</td>
              <td>{{ s.quizzes_taken }}</td>
              <td>
                <span v-if="s.avg_score !== null" :class="{'text-success': s.avg_score >= 70, 'text-danger': s.avg_score < 70}">
                  {{ s.avg_score }}%
                </span>
                <span v-else class="text-muted">--</span>
              </td>
              <td>{{ s.completed_items }}</td>
              <td>{{ s.joined }}</td>
            </tr>
          </tbody>
        </table>
        <p v-else class="empty-state">No students found matching your search.</p>
      </div>

      <!-- Quick Links -->
      <div class="quick-links">
        <RouterLink to="/manage-courses" class="btn btn-primary">Manage Courses / Content</RouterLink>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import apiClient from '@/api'; 
import { RouterLink } from 'vue-router';

const summary = ref({});
const allStudents = ref([]);
const discussions = ref([]);
const isLoading = ref(true);
const isLoadingStudents = ref(true);
const isLoadingDiscussions = ref(true);
const error = ref('');
const searchQuery = ref('');

const unansweredCount = computed(() => discussions.value.filter(d => !d.answered).length);

const filteredStudents = computed(() => {
  if (!searchQuery.value) return allStudents.value;
  const q = searchQuery.value.toLowerCase();
  return allStudents.value.filter(s => 
    s.name.toLowerCase().includes(q) || s.email.toLowerCase().includes(q)
  );
});

const fetchSummary = async () => {
    try {
        const response = await apiClient.get('/teacher/dashboard-summary');
        summary.value = response.data;
    } catch (err) {
        error.value = "Failed to load dashboard insights.";
    } finally {
        isLoading.value = false;
    }
};

const fetchStudents = async () => {
    isLoadingStudents.value = true;
    try {
        const response = await apiClient.get('/teacher/students');
        allStudents.value = response.data;
    } catch (err) {
        console.error("Failed to load students list:", err);
    } finally {
        isLoadingStudents.value = false;
    }
};

const fetchDiscussions = async () => {
    isLoadingDiscussions.value = true;
    try {
        const response = await apiClient.get('/teacher/discussions');
        discussions.value = response.data;
    } catch (err) {
        console.error('Failed to load discussions:', err);
    } finally {
        isLoadingDiscussions.value = false;
    }
};

onMounted(() => {
    fetchSummary();
    fetchStudents();
    fetchDiscussions();
});
</script>

<style scoped>
.dashboard-container { max-width: 1200px; margin: 2rem auto; padding: 1rem; }
.summary-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1.5rem; margin-bottom: 2rem; }
.summary-card { background: white; padding: 1.5rem; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); text-align: center; }
.stat-value { font-size: 2.5rem; font-weight: bold; color: #007bff; margin-bottom: 0.5rem; }
.stat-label { color: #6c757d; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 1px; }

.dashboard-widgets { display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; margin-bottom: 2rem; }
@media(max-width: 768px) {
  .dashboard-widgets { grid-template-columns: 1fr; }
}
.widget { background: white; padding: 1.5rem; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
.widget h2 { margin-top: 0; margin-bottom: 0.5rem; font-size: 1.25rem; }
.text-sm { font-size: 0.85rem; }
.text-gray { color: #6c757d; }

/* Student links */
.student-name-link { color: #007bff; text-decoration: none; font-weight: 600; }
.student-name-link:hover { text-decoration: underline; color: #0056b3; }
.student-email, .cell-email { display: block; font-size: 0.8rem; color: #6c757d; }
.student-info { display: flex; flex-direction: column; }

.risk-list { list-style: none; padding: 0; }
.risk-list li { display: flex; justify-content: space-between; align-items: center; padding: 0.75rem 0; border-bottom: 1px solid #eee; }
.risk-list li:last-child { border-bottom: none; }
.risk-badge { padding: 0.25rem 0.5rem; border-radius: 12px; font-size: 0.75rem; text-transform: uppercase; font-weight: bold; }
.high_risk { background-color: #f8d7da; color: #721c24; }
.medium_risk { background-color: #fff3cd; color: #856404; }

.activity-table { width: 100%; border-collapse: collapse; margin-top: 1rem; }
.activity-table th, .activity-table td { padding: 0.75rem; text-align: left; border-bottom: 1px solid #eee; }
.activity-table th { color: #6c757d; font-size: 0.85rem; text-transform: uppercase; }
.text-success { color: #28a745; font-weight: bold; }
.text-danger { color: #dc3545; font-weight: bold; }
.text-warning { color: #ffc107; }
.text-muted { color: #adb5bd; }

/* All Students section */
.full-width-widget { margin-bottom: 2rem; }
.students-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; flex-wrap: wrap; gap: 1rem; }
.students-header h2 { margin: 0; }
.search-input { padding: 0.5rem 1rem; border: 1px solid #ccc; border-radius: 20px; font-size: 0.9rem; width: 280px; }
.clickable-row { cursor: pointer; transition: background 0.15s; }
.clickable-row:hover { background-color: #f0f7ff; }
.student-name-col { font-weight: 600; color: #007bff; }

.empty-state { color: #6c757d; font-style: italic; margin-top: 1rem; }

.quick-links { margin-top: 2rem; padding-top: 2rem; border-top: 1px solid #eee; text-align: center; }
.btn { display: inline-block; padding: 0.75rem 1.5rem; border-radius: 5px; text-decoration: none; font-weight: bold; cursor: pointer; border: none; }
.btn-primary { background-color: #007bff; color: white; }
.btn-primary:hover { background-color: #0056b3; }

.loading, .error-message { text-align: center; padding: 3rem; font-size: 1.1rem; }
.error-message { color: #dc3545; }

/* Student Queries */
.queries-widget { border-left: 4px solid #17a2b8; }
.queries-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }
.queries-header h2 { margin: 0; }
.unanswered-counter { background: #dc3545; color: white; padding: 0.25rem 0.75rem; border-radius: 12px; font-size: 0.85rem; font-weight: bold; }
.queries-list { display: flex; flex-direction: column; gap: 0.75rem; }
.query-item { display: flex; justify-content: space-between; align-items: center; padding: 1rem; border-radius: 6px; border: 1px solid #e9ecef; gap: 1rem; }
.query-item.unanswered { border-left: 3px solid #dc3545; background: #fff8f8; }
.query-info { flex: 1; }
.query-title-row { display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.25rem; }
.query-title { font-weight: 600; font-size: 1rem; }
.badge-unanswered { background: #dc3545; color: white; padding: 0.1rem 0.4rem; border-radius: 4px; font-size: 0.65rem; font-weight: bold; }
.badge-answered { background: #28a745; color: white; padding: 0.1rem 0.4rem; border-radius: 4px; font-size: 0.65rem; font-weight: bold; }
.query-preview { margin: 0.25rem 0; color: #555; font-size: 0.85rem; }
.query-meta { display: flex; gap: 1rem; font-size: 0.8rem; color: #6c757d; flex-wrap: wrap; }
.query-course { font-weight: 500; color: #007bff; }
.btn-sm { padding: 0.4rem 0.8rem; font-size: 0.85rem; }
.btn-answer { background: #17a2b8; color: white; text-decoration: none; border-radius: 4px; white-space: nowrap; }
.btn-answer:hover { background: #138496; }
</style>