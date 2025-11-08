<template>
  <div class="builder-container">
    <div v-if="isLoading">Loading Assessment...</div>
    <div v-else-if="error">{{ error }}</div>
    <div v-else>
      <h1>Assessment Builder: {{ assessment.title }}</h1>
      <p>Course: {{ assessment.course_title }}</p>

      <div class="card quiz-builder">
        <div class="question-list">
          <div v-for="(q, index) in assessment.assessment_data.questions" :key="index" class="question-preview">
            <strong>Q{{index+1}}:</strong> {{ q.text }}
            <button @click.prevent="removeQuestion(index)" class="btn-remove-q">x</button>
          </div>
          <p v-if="!assessment.assessment_data.questions.length">No questions yet.</p>
        </div>
        <div class="new-question-form">
          <h5>Add a Question</h5>
          <input v-model="newQuestion.text" placeholder="Question text..." />
          <input v-model="newQuestion.options[0]" placeholder="Option 1" />
          <input v-model="newQuestion.options[1]" placeholder="Option 2" />
          <input v-model="newQuestion.options[2]" placeholder="Option 3" />
          <div class="correct-answer-selector">
            <strong>Correct Answer:</strong>
            <label v-for="i in 3" :key="i"><input type="radio" :value="i-1" v-model="newQuestion.correct_answer_index" name="correct-answer" /> Option {{i}}</label>
          </div>
          <button @click.prevent="addQuestion" class="btn-add-q">Add Question</button>
        </div>
      </div>
      
      <div class="actions">
        <RouterLink :to="{ name: 'manage-courses' }" class="btn-secondary">Back to Courses</RouterLink>
        <button @click="saveAssessment" class="btn">Save Assessment</button>
      </div>
      <p v-if="message" class="message success">{{ message }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRoute, RouterLink } from 'vue-router';
import apiClient from '@/api';

const route = useRoute();
const assessment = ref(null);
const isLoading = ref(true);
const error = ref('');
const message = ref('');

const defaultQuestionState = () => ({ text: '', options: ['', '', ''], correct_answer_index: null });
const newQuestion = ref(defaultQuestionState());

const fetchAssessment = async () => {
  try {
    const response = await apiClient.get(`/assessments/${route.params.assessmentId}`);
    assessment.value = response.data;
  } catch (err) { error.value = "Failed to load assessment."; }
  finally { isLoading.value = false; }
};

const addQuestion = () => {
  if (!newQuestion.value.text || newQuestion.value.options.some(o => !o) || newQuestion.value.correct_answer_index === null) {
    alert('Please fill all question fields and select a correct answer.');
    return;
  }
  const questionWithId = { ...newQuestion.value, id: `q${Date.now()}` };
  assessment.value.assessment_data.questions.push(questionWithId);
  newQuestion.value = defaultQuestionState();
};

const removeQuestion = (index) => {
  assessment.value.assessment_data.questions.splice(index, 1);
};

const saveAssessment = async () => {
  try {
    const response = await apiClient.put(`/assessments/${assessment.value.id}`, {
      assessment_data: assessment.value.assessment_data
    });
    message.value = response.data.message;
    setTimeout(() => message.value = '', 4000);
  } catch (err) {
    error.value = "Failed to save assessment.";
  }
};

onMounted(fetchAssessment);
</script>

<style scoped>
/* Reusing styles from CourseManagementView for consistency */
.builder-container { max-width: 800px; margin: 2rem auto; }
.card { background: #fff; padding: 1.5rem; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
.quiz-builder { border: 1px solid #e9ecef; padding: 1rem; margin-top: 1rem; border-radius: 5px; background: #f8f9fa; }
.new-question-form { margin-top: 1rem; padding-top: 1rem; border-top: 1px dashed #ccc; }
.new-question-form h5 { margin-top: 0; }
.new-question-form input[type="text"] { margin-bottom: 0.5rem; width: 100%; padding: 0.75rem; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; }
.correct-answer-selector { font-size: 0.9em; margin: 0.5rem 0; }
.correct-answer-selector label { margin-right: 1rem; }
.btn-add-q { background-color: #28a745; color: white; border: none; padding: 0.5rem 1rem; border-radius: 4px; cursor: pointer; }
.question-preview { display: flex; justify-content: space-between; align-items: center; background: #fff; padding: 0.5rem; border-radius: 4px; margin-bottom: 0.5rem; }
.btn-remove-q { background-color: #dc3545; color: white; border: none; border-radius: 50%; width: 20px; height: 20px; cursor: pointer; }
.actions { margin-top: 2rem; display: flex; justify-content: space-between; }
.btn { background-color: #007bff; color: white; padding: 0.75rem 1.5rem; border: none; border-radius: 4px; cursor: pointer; }
.btn-secondary { background-color: #6c757d; color: white; padding: 0.75rem 1.5rem; border: none; border-radius: 4px; text-decoration: none; }
.message { padding: 1rem; border-radius: 4px; text-align: center; margin-top: 1rem; }
.success { background-color: #d4edda; color: #155724; }
</style>