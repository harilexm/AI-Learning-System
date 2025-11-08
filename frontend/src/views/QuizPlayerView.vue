<template>
  <div class="quiz-container">
    <div v-if="isLoading" class="state-message">Loading Quiz...</div>
    <div v-else-if="error" class="state-message error">{{ error }}</div>
    
    <!-- Quiz Taking Interface -->
    <div v-else-if="quiz && !results">
      <h1>{{ quiz.title }}</h1>
      <div v-for="(question, index) in quiz.questions" :key="question.id" class="question-card">
        <h3>Question {{ index + 1 }}</h3>
        <p class="question-text">{{ question.text }}</p>
        <div class="options">
          <label v-for="(option, optIndex) in question.options" :key="optIndex" class="option">
            <input type="radio" :name="question.id" :value="optIndex" v-model="studentAnswers[question.id]">
            <span>{{ option }}</span>
          </label>
        </div>
      </div>
      <button @click="submitQuiz" class="btn-submit">Submit Answers</button>
    </div>

    <!-- Quiz Results Interface -->
    <div v-else-if="results" class="results-container">
      <h1>Quiz Results for "{{ quiz.title }}"</h1>
      <h2 class="score">Your Score: {{ results.score }}%</h2>
      <p class="summary">You answered {{ Math.round(results.score / 100 * results.total_questions) }} out of {{ results.total_questions }} questions correctly.</p>

      <div v-for="(question, index) in quiz.questions" :key="question.id" class="question-card result-card">
        <h3>Question {{ index + 1 }}</h3>
        <p class="question-text">{{ question.text }}</p>
        <div class="options">
          <div v-for="(option, optIndex) in question.options" :key="optIndex" 
               class="option"
               :class="{
                 correct: optIndex === results.correct_answers[question.id],
                 incorrect: optIndex !== results.correct_answers[question.id] && optIndex === parseInt(results.student_answers[question.id])
               }">
            <span>{{ option }}</span>
            <span v-if="optIndex === results.correct_answers[question.id]"> (Correct Answer)</span>
            <span v-if="optIndex !== results.correct_answers[question.id] && optIndex === parseInt(results.student_answers[question.id])"> (Your Answer)</span>
          </div>
        </div>
      </div>
       <RouterLink to="/dashboard" class="btn-back">Back to Dashboard</RouterLink>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRoute, RouterLink } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import axios from 'axios';

const route = useRoute();
const authStore = useAuthStore();
const quiz = ref(null);
const studentAnswers = ref({});
const results = ref(null);
const isLoading = ref(true);
const error = ref('');

const apiClient = axios.create({ baseURL: 'http://localhost:5000/api', headers: { Authorization: `Bearer ${authStore.token}` } });

onMounted(async () => {
  const contentId = route.params.contentId;
  try {
    const response = await apiClient.get(`/quizzes/${contentId}`);
    quiz.value = response.data;
    // Initialize studentAnswers object
    quiz.value.questions.forEach(q => studentAnswers.value[q.id] = null);
  } catch (err) {
    error.value = "Failed to load the quiz.";
  } finally {
    isLoading.value = false;
  }
});

const submitQuiz = async () => {
  const contentId = route.params.contentId;
  try {
    const response = await apiClient.post(`/quizzes/${contentId}/submit`, { answers: studentAnswers.value });
    results.value = response.data;
  } catch (err) {
    error.value = "Failed to submit the quiz.";
  }
};
</script>

<style scoped>
.quiz-container { max-width: 800px; margin: 2rem auto; padding: 2rem; background: #fff; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
.state-message { text-align: center; font-size: 1.2rem; padding: 2rem; }
.error { color: #dc3545; }
.question-card { margin-bottom: 2rem; padding-bottom: 1rem; border-bottom: 1px solid #eee; }
.question-text { font-size: 1.1em; }
.options { display: flex; flex-direction: column; gap: 0.5rem; margin-top: 1rem; }
.option { display: block; padding: 0.75rem; border: 1px solid #ccc; border-radius: 5px; cursor: pointer; }
.option input { margin-right: 0.5rem; }
.btn-submit { background-color: #28a745; color: white; padding: 0.75rem 1.5rem; border: none; border-radius: 5px; font-size: 1.1em; cursor: pointer; display: block; width: 100%; }
.results-container .score { color: #007bff; text-align: center; font-size: 2em; }
.results-container .summary { text-align: center; font-size: 1.1em; color: #6c757d; }
.result-card .option.correct { background-color: #d4edda; border-color: #c3e6cb; font-weight: bold; }
.result-card .option.incorrect { background-color: #f8d7da; border-color: #f5c6cb; text-decoration: line-through; }
.btn-back { display: inline-block; margin-top: 2rem; text-decoration: none; color: #007bff; }
</style>