<template>
  <div class="course-detail-container">
    <!-- Loading State -->
    <div v-if="isLoading" class="loading-state">
      <h2>Loading course details...</h2>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="error-state">
      <h2>Something went wrong</h2>
      <p>{{ error }}</p>
      <RouterLink to="/dashboard">Back to Dashboard</RouterLink>
    </div>
    
    <!-- Success State -->
    <div v-else-if="course" class="course-content">
      <div style="display: flex; justify-content: space-between; align-items: baseline; flex-wrap: wrap; gap: 0.5rem;">
        <h1 class="course-title">{{ course.title }}</h1>
        <div style="display: flex; gap: 0.5rem; align-items: center;">
          <RouterLink :to="{ name: 'course-discussions', params: { courseId: course.id } }" class="btn-discussions">
            Discussions
          </RouterLink>
          <RouterLink v-if="authStore.isStudent" :to="{ name: 'course-study-plan', params: { courseId: course.id } }" class="btn-study-plan">
            Generate Study Plan
          </RouterLink>
        </div>
      </div>
      <p class="course-description">{{ course.description }}</p>
      
      <!-- Loop through Modules -->
      <div v-for="module in course.modules" :key="module.id" class="module-container">
        <h2>Module {{ module.order }}: {{ module.title }}</h2>
        <p v-if="module.description" class="module-description">{{ module.description }}</p>

        <!-- Loop through Learning Content in each Module -->
        <ul v-if="module.learning_contents && module.learning_contents.length" class="content-list">
          <li v-for="content in module.learning_contents" :key="content.id" class="content-item">
            <span class="content-type-icon">{{ getIconFor(content.type) }}</span>
            <div class="content-info">
              <span class="content-title">{{ content.order }}. {{ content.title }}</span>
              <a v-if="content.type === 'video' && content.url" :href="content.url" target="_blank" class="content-link">
                Watch Video &rarr;
              </a>
              <!-- Button for articles -->
              <a v-if="content.type === 'article'" @click.prevent="toggleArticle(content.id)" href="#" class="content-link">
                {{ expandedArticles[content.id] ? 'Hide Article' : 'Read Article' }}
              </a>
            </div>
            
            <!-- Action Buttons -->
            <div class="content-action">
              <template v-if="authStore.isStudent">
                <RouterLink v-if="content.type === 'quiz'" :to="{ name: 'quiz-player', params: { contentId: content.id } }" class="btn-quiz">
                  Start Quiz
                </RouterLink>
                <template v-else>
                  <button v-if="content.progress_status !== 'completed'" @click="markAsComplete(content.id)" class="btn-complete">
                    Mark as Complete
                  </button>
                  <span v-else class="status-completed">
                    Completed ✔️
                  </span>
                </template>
              </template>
            </div>
            <div v-if="content.type === 'article' && expandedArticles[content.id]" class="article-body">
              <div v-html="sanitize(content.body)"></div>
              <ChatbotWidget :article-context="content.body" />
            </div>
          </li>
        </ul>
        <div v-else class="no-content">
            <p>No learning content has been added to this module yet.</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRoute, RouterLink } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import apiClient from '@/api';
import ChatbotWidget from '@/components/ChatbotWidget.vue';
import DOMPurify from 'dompurify';

const route = useRoute();
const authStore = useAuthStore();
const course = ref(null);
const isLoading = ref(true);
const error = ref('');
const expandedArticles = ref({});

const toggleArticle = (contentId) => {
  expandedArticles.value[contentId] = !expandedArticles.value[contentId];
};

const sanitize = (html) => DOMPurify.sanitize(html);

const fetchCourseDetails = async () => {
  const courseId = route.params.courseId;
  try {
    const response = await apiClient.get(`/courses/${courseId}`);
    if (response.data && response.data.modules) {
        course.value = response.data;
    } else {
        throw new Error("Invalid course data received from server.");
    }
  } catch (err) {
    console.error("API Error fetching course details:", err);
    error.value = 'Failed to load course details. The course may not exist or an error occurred.';
  } finally {
    isLoading.value = false;
  }
};

const markAsComplete = async (contentId) => {
  try {
    await apiClient.post(`/progress/${contentId}/complete`);
    for (const module of course.value.modules) {
      const contentItem = module.learning_contents.find(c => c.id === contentId);
      if (contentItem) {
        contentItem.progress_status = 'completed';
        break;
      }
    }
  } catch (err) {
    alert('Could not update progress. Please try again.');
  }
};

const getIconFor = (type) => {
  switch (type) {
    case 'video': return '▶️';
    case 'article': return '📄';
    case 'quiz': return '❓';
    default: return '🔗';
  }
};

onMounted(fetchCourseDetails);
</script>

<style scoped>
.course-detail-container { max-width: 900px; margin: 2rem auto; padding: 1rem; }
.loading-state, .error-state { text-align: center; padding: 4rem; color: #6c757d; }
.article-body {flex-basis: 100%; margin-top: 1rem; padding: 1.5rem; background-color: #f8f9fa; border-radius: 5px; border: 1px solid #e9ecef; line-height: 1.6;}
.content-item {flex-wrap: wrap;}
.course-title { font-size: 2.5rem; margin-bottom: 0.5rem; color: #2c3e50; }
.btn-study-plan { background: linear-gradient(135deg, #6f42c1, #007bff); color: white; padding: 0.5rem 1rem; border-radius: 8px; font-weight: bold; text-decoration: none; box-shadow: 0 4px 6px rgba(0,0,0,0.1); transition: transform 0.2s; }
.btn-study-plan:hover { transform: translateY(-2px); }
.btn-discussions { background: linear-gradient(135deg, #20c997, #17a2b8); color: white; padding: 0.5rem 1rem; border-radius: 8px; font-weight: bold; text-decoration: none; box-shadow: 0 4px 6px rgba(0,0,0,0.1); transition: transform 0.2s; }
.btn-discussions:hover { transform: translateY(-2px); }
.course-description { font-size: 1.1rem; color: #6c757d; margin-bottom: 3rem; margin-top: 1rem; }
.module-container { background: #fff; border-radius: 8px; padding: 1.5rem 2rem; margin-bottom: 2rem; box-shadow: 0 4px 12px rgba(0,0,0,0.08); }
.module-container h2 { margin-top: 0; border-bottom: 1px solid #eee; padding-bottom: 1rem; }
.module-description { font-style: italic; color: #6c757d; }
.content-list { list-style: none; padding: 0; margin-top: 1rem; }
.no-content { color: #888; font-style: italic; padding: 1rem 0;}
.content-item { display: flex; align-items: center; padding: 1rem 0; border-bottom: 1px solid #f1f1f1; }
.content-item:last-child { border-bottom: none; }
.content-type-icon { font-size: 1.5rem; margin-right: 1.5rem; }
.content-info { flex-grow: 1; }
.content-title { font-weight: 500; display: block; }
.content-link { font-size: 0.9rem; color: #007bff; text-decoration: none; font-weight: bold; }
.content-action { margin-left: auto; white-space: nowrap; }
.btn-complete { background-color: #007bff; color: white; border: none; padding: 0.5rem 1rem; border-radius: 5px; cursor: pointer; font-weight: 500; }
.btn-complete:hover { background-color: #0056b3; }
.status-completed { color: #28a745; font-weight: bold; padding: 0.5rem 1rem; }
.btn-quiz { background-color: #17a2b8; color: white; border: none; padding: 0.5rem 1rem; border-radius: 5px; cursor: pointer; font-weight: 500; text-decoration: none; }
</style>