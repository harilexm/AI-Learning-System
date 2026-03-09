<template>
  <div class="course-mgmt-container">
    <h1>Course Management</h1>
    
    <div class="main-grid">
      <!-- Left Column: Course List and Creation -->
      <div class="course-list-panel">
        <div class="card">
          <h2>Create a New Course</h2>
          <form @submit.prevent="handleCreateCourse">
            <div class="form-group">
              <label for="courseTitle">Course Title</label>
              <input id="courseTitle" v-model="newCourse.title" type="text" required />
            </div>
            <div class="form-group">
              <label for="courseDesc">Course Description</label>
              <textarea id="courseDesc" v-model="newCourse.description"></textarea>
            </div>
            <button type="submit" class="btn">Create Course</button>
          </form>
        </div>

        <div class="card">
          <h2>Existing Courses</h2>
          <div v-if="isLoadingCourses">Loading...</div>
          <ul v-else-if="courses.length > 0" class="course-list">
            <li v-for="course in courses" :key="course.id" @click="selectCourse(course.id)" :class="{ selected: selectedCourse?.id === course.id }">
                    <!-- Title is now wrapped in a span -->
            <span>{{ course.title }}</span>
            
            <!-- The new delete button is added -->
            <button @click="openEditModal(course)" class="btn-edit" title="Edit Course">✏️</button>
            <button @click.stop="handleDeleteCourse(course.id)" class="btn-delete" title="Delete Course">x</button>
            </li>
          </ul>
          <p v-else>No courses created yet.</p>
        </div>
      </div>

      <!-- Right Column: Course Builder -->
      <div class="course-builder-panel">
        <div v-if="!selectedCourse" class="card placeholder">
          <p>Select a course on the left to start building.</p>
        </div>
        
        <div v-else>
          <h2>Building: {{ selectedCourse.title }}</h2>
          <RouterLink :to="{ name: 'course-progress', params: { courseId: selectedCourse.id } }" class="btn btn-secondary">
            View Student Progress
          </RouterLink>
          
          <!-- Modules Section -->
          <div v-for="module in selectedCourse.modules" :key="module.id" class="card module-card">
            <h3>Module {{ module.order }}: {{ module.title }}</h3>
            <button @click="handleDeleteModule(module.id)" class="btn-delete" title="Delete Module">x</button>
            <ul class="content-list">
              <li v-for="content in module.learning_contents" :key="content.id" class="content-item">
                <span>{{ content.order }}. {{ content.title }} ({{ content.type }})</span>
                <button @click="handleDeleteContent(content.id)" class="btn-delete" title="Delete Content Item">x</button>
              </li>
              <li v-if="!module.learning_contents.length" class="content-item-empty">No content yet.</li>
            </ul>

            <!-- ADD NEW CONTENT FORM (CORRECTED) -->
            <form @submit.prevent="handleAddContent(module.id)" class="add-content-form">
              <h4>Add New Content to "{{ module.title }}"</h4>
              <input v-model="newContent[module.id].title" type="text" placeholder="Content Title" required/>
              <!-- THIS IS THE FIX: The 'Quiz' option is now present -->
              <select v-model="newContent[module.id].type">
                <option value="video">Video</option>
                <option value="article">Article</option>
                <option value="quiz">Quiz</option>
              </select>
              <!-- ADD THIS NEW FORM GROUP -->
              <div class="form-group tag-group">
                <label>Tags (comma-separated)</label>
                <input v-model="newContent[module.id].tags" type="text" placeholder="e.g., algebra, intro, calculus" />
              </div>

              <!-- Conditional fields based on type -->
              <input v-if="newContent[module.id].type === 'video'" v-model="newContent[module.id].url" type="text" placeholder="Video URL" />
              <textarea v-if="newContent[module.id].type === 'article'" v-model="newContent[module.id].body" placeholder="Article content..."></textarea>
              <button 
                  v-if="newContent[module.id].body && newContent[module.id].body.length >= 100" 
                  @click.prevent="handleGenerateQuiz(module.id)" 
                  class="btn-generate-quiz"
                  :disabled="isGeneratingQuiz">
                  {{ isGeneratingQuiz ? 'Generating...' : '🤖 Generate Quiz from this Article' }}
                </button>
              <!-- QUIZ BUILDER UI -->
              <div v-if="newContent[module.id].type === 'quiz'" class="quiz-builder">
                <div class="question-list">
                  <div v-for="(q, index) in newContent[module.id].quiz_data.questions" :key="index" class="question-preview">
                    <strong>Q{{index+1}}:</strong> {{ q.text }} 
                    <button @click.prevent="removeQuestion(module.id, index)" class="btn-remove-q" title="Remove Question">x</button>
                  </div>
                </div>
                <div class="new-question-form">
                  <h5>Add a Question</h5>
                  <input v-model="newQuestion.text" placeholder="Question text..." />
                  <input v-model="newQuestion.options[0]" placeholder="Option 1" />
                  <input v-model="newQuestion.options[1]" placeholder="Option 2" />
                  <input v-model="newQuestion.options[2]" placeholder="Option 3" />
                  <div class="correct-answer-selector">
                    <strong>Correct Answer:</strong>
                    <label v-for="i in 3" :key="i">
                      <input type="radio" :value="i-1" v-model="newQuestion.correct_answer_index" name="correct-answer" /> Option {{i}}
                    </label>
                  </div>
                  <button @click.prevent="addQuestionToContent(module.id)" class="btn-add-q">Add Question to Quiz</button>
                </div>
              </div>

              <button type="submit" class="btn-small">Save New Content</button>
            </form>
          </div>
          
          <div class="card">
            <h2>Add New Module</h2>
            <form @submit.prevent="handleAddModule">
              <input v-model="newModule.title" type="text" placeholder="Module Title" required />
              <button type="submit" class="btn">Add Module</button>
            </form>
          </div>
        </div>
      </div>
    </div>
    
    <p v-if="message" class="message" :class="isError ? 'error' : 'success'">{{ message }}</p>
    <div v-if="isEditingCourse" class="modal-overlay" @click.self="isEditingCourse = false">
      <div class="modal-content">
        <h2>Edit Course</h2>
        <form @submit.prevent="handleUpdateCourse">
          <div class="form-group">
            <label for="editCourseTitle">Course Title</label>
            <input id="editCourseTitle" v-model="editingCourseData.title" type="text" required />
          </div>
          <div class="form-group">
            <label for="editCourseDesc">Course Description</label>
            <textarea id="editCourseDesc" v-model="editingCourseData.description"></textarea>
          </div>
          <div class="modal-actions">
            <button type="button" class="btn-secondary" @click="isEditingCourse = false">Cancel</button>
            <button type="submit" class="btn">Save Changes</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { RouterLink } from 'vue-router';
import apiClient from '@/api';

const courses = ref([]);
const selectedCourse = ref(null);
const isLoadingCourses = ref(true);
const message = ref('');
const isError = ref(false);
const newCourse = ref({ title: '', description: '' });
const newModule = ref({ title: '', description: '' });
const newContent = ref({});
const defaultQuestionState = () => ({ text: '', options: ['', '', ''], correct_answer_index: null });
const newQuestion = ref(defaultQuestionState());
const isGeneratingQuiz = ref(false);
const isEditingCourse = ref(false);
const editingCourseData = ref({ id: null, title: '', description: '' });

// API HELPER FUNCTIONS
const showApiMessage = (msg, error = false) => {
  message.value = msg;
  isError.value = error;
  setTimeout(() => message.value = '', 4000);
};

const openEditModal = (course) => {
  // Create a copy of the course data to avoid modifying the original list directly
  editingCourseData.value = { ...course };
  isEditingCourse.value = true;
};

const handleUpdateCourse = async () => {
  if (!editingCourseData.value.id) return;
  try {
    await apiClient.put(`/courses/${editingCourseData.value.id}`, {
      title: editingCourseData.value.title,
      description: editingCourseData.value.description
    });
    showApiMessage('Course updated successfully.');
    isEditingCourse.value = false; // Close the modal
    await fetchCourses(); // Refresh the course list
  } catch (err) {
    handleApiError(err, 'Failed to update course.');
  }
};

const handleApiError = (err, defaultMsg) => {
  const errorMsg = err.response?.data?.error || defaultMsg;
  showApiMessage(errorMsg, true);
};

const fetchCourses = async () => {
  isLoadingCourses.value = true;
  try {
    const response = await apiClient.get('/courses');
    courses.value = response.data;
  } catch (err) { 
    handleApiError(err, 'Failed to load courses.'); 
  } finally {
    isLoadingCourses.value = false;
  }
};

// AI QUIZ GENERATION METHOD
const handleGenerateQuiz = async (moduleId) => {
  const articleText = newContent.value[moduleId].body;
  if (!articleText || articleText.length < 100) {
    showApiMessage('Article text must be at least 100 characters long to generate a quiz.', true);
    return;
  }

  isGeneratingQuiz.value = true;
  try {
    const response = await apiClient.post('/ai/generate-quiz', { text: articleText });
    const aiQuizData = response.data;

    // Validate the AI response
    if (aiQuizData && aiQuizData.questions) {
      // Update the state to transform the UI from an article editor to a quiz builder
      newContent.value[moduleId].type = 'quiz';
      newContent.value[moduleId].quiz_data = aiQuizData;
      showApiMessage('Quiz generated successfully! Please review before saving.');
    } else {
      throw new Error("AI response was not in the expected format.");
    }
  } catch (err) {
    handleApiError(err, 'Failed to generate quiz from AI.');
  } finally {
    isGeneratingQuiz.value = false;
  }
};


const selectCourse = async (courseId) => {
  try {
    const response = await apiClient.get(`/courses/${courseId}`);
    selectedCourse.value = response.data;
    selectedCourse.value.modules.forEach(module => {
      newContent.value[module.id] = { 
        title: '', 
        type: 'video', 
        url: '', 
        body: '', 
        quiz_data: { questions: [] },
        tags: '' 
      };
    });
  } catch (err) { 
    handleApiError(err, 'Failed to load course details.'); 
  }
};

const handleCreateCourse = async () => {
  try {
    await apiClient.post('/courses', newCourse.value);
    showApiMessage('Course created successfully.');
    newCourse.value = { title: '', description: '' };
    await fetchCourses();
  } catch (err) { 
    handleApiError(err, 'Failed to create course.'); 
  }
};

const handleAddModule = async () => {
  const nextOrder = (selectedCourse.value.modules.length || 0) + 1;
  const payload = { ...newModule.value, moduleOrder: nextOrder };
  try {
    await apiClient.post(`/courses/${selectedCourse.value.id}/modules`, payload);
    showApiMessage('Module added successfully.');
    newModule.value.title = '';
    await selectCourse(selectedCourse.value.id);
  } catch (err) { 
    handleApiError(err, 'Failed to add module.'); 
  }
};

const handleAddContent = async (moduleId) => {
  const module = selectedCourse.value.modules.find(m => m.id === moduleId);
  const nextOrder = (module.learning_contents.length || 0) + 1;
  const contentData = newContent.value[moduleId];

  if (contentData.type === 'quiz' && contentData.quiz_data.questions.length === 0) {
      showApiMessage('A quiz must have at least one question before saving.', true);
      return;
  }

  // Build the payload with the field names expected by the backend
  const payload = {
    title: contentData.title,
    type: contentData.type,
    contentOrder: nextOrder,
    contentUrl: contentData.url || null,
    contentBody: contentData.body || null,
    quizData: contentData.type === 'quiz' ? contentData.quiz_data : null,
    tags: contentData.tags || null
  };

  try {
    await apiClient.post(`/modules/${moduleId}/content`, payload);
    showApiMessage('Content added successfully.');
    newContent.value[moduleId] = { title: '', type: 'video', url: '', body: '', quiz_data: { questions: [] }, tags: '' };
    await selectCourse(selectedCourse.value.id);
  } catch (err) { 
    handleApiError(err, 'Failed to add content.'); 
  }
};

// QUIZ BUILDER METHODS
const addQuestionToContent = (moduleId) => {
  if (!newQuestion.value.text || newQuestion.value.options.some(o => !o) || newQuestion.value.correct_answer_index === null) {
    showApiMessage('Please fill all question fields and select a correct answer.', true);
    return;
  }
  const questionWithId = { ...newQuestion.value, id: `q${Date.now()}` };
  newContent.value[moduleId].quiz_data.questions.push(questionWithId);
  newQuestion.value = defaultQuestionState();
};

const removeQuestion = (moduleId, questionIndex) => {
  newContent.value[moduleId].quiz_data.questions.splice(questionIndex, 1);
};

// DELETE METHODS
const handleDeleteCourse = async (courseId) => {
  if (confirm('Are you sure you want to delete this entire course? This action cannot be undone.')) {
    try {
      await apiClient.delete(`/courses/${courseId}`);
      showApiMessage('Course deleted successfully.');
      selectedCourse.value = null; // Deselect if the current course was deleted
      await fetchCourses(); // Refresh the list
    } catch (err) {
      handleApiError(err, 'Failed to delete course.');
    }
  }
};

const handleDeleteModule = async (moduleId) => {
  if (confirm('Are you sure you want to delete this module and all its content?')) {
    try {
      await apiClient.delete(`/modules/${moduleId}`);
      showApiMessage('Module deleted successfully.');
      // Refresh the details of the currently selected course
      await selectCourse(selectedCourse.value.id);
    } catch (err) {
      handleApiError(err, 'Failed to delete module.');
    }
  }
};

const handleDeleteContent = async (contentId) => {
  if (confirm('Are you sure you want to delete this content item?')) {
    try {
      await apiClient.delete(`/content/${contentId}`);
      showApiMessage('Content item deleted successfully.');
      // Refresh the details of the currently selected course
      await selectCourse(selectedCourse.value.id);
    } catch (err) {
      handleApiError(err, 'Failed to delete content item.');
    }
  }
};

onMounted(fetchCourses);

</script>

<style scoped>
.tag-group {margin-top: 1rem;}
.btn-generate-quiz {display: block; width: 100%; margin-top: 0.5rem; padding: 0.75rem; background-color: #6f42c1; color: white;border: none; border-radius: 4px; cursor: pointer; font-weight: bold;}
.btn-generate-quiz:disabled { background-color: #b39ddb; cursor: not-allowed;}
.course-list li { padding: 0.8rem 0.5rem;}
.course-title { flex-grow: 1; cursor: pointer; padding: 0 0.5rem;}
.course-actions { display: flex; align-items: center; gap: 0.5rem; visibility: hidden; opacity: 0; transition: opacity 0.2s;}
.course-list li:hover .course-actions { visibility: visible; opacity: 1;}
.btn-edit { background: none; border: none; cursor: pointer; font-size: 1rem;}
.btn-delete { visibility: visible; opacity: 1;}
.modal-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background-color: rgba(0, 0, 0, 0.6); display: flex; justify-content: center; align-items: center; z-index: 1001;}
.modal-content { background: white; padding: 2rem; border-radius: 8px; width: 100%; max-width: 500px;}
.modal-actions { display: flex; justify-content: flex-end; gap: 1rem; margin-top: 1.5rem;}
.course-list li, .module-header, .content-item { display: flex; justify-content: space-between; align-items: center;}
.btn-delete { background-color: transparent; color: #dc3545; border: none; border-radius: 50%; width: 24px; height: 24px; cursor: pointer; font-weight: bold; line-height: 24px; text-align: center; visibility: hidden; opacity: 0; transition: opacity 0.2s;}
.course-list li:hover .btn-delete,
.module-card:hover .module-header .btn-delete,
.content-item:hover .btn-delete { visibility: visible; opacity: 1;}
.btn-delete:hover { background-color: #f8d7da;}
.main-grid { display: grid; grid-template-columns: 350px 1fr; gap: 2rem; align-items: flex-start; }
.course-list-panel .card { margin-bottom: 1rem; }
.course-builder-panel .placeholder { text-align: center; padding: 4rem; color: #888; }
.course-list { list-style: none; padding: 0; margin: 0; }
.course-list li { padding: 0.8rem 1rem; border-radius: 5px; cursor: pointer; border: 1px solid transparent; }
.course-list li:hover { background-color: #f8f9fa; }
.course-list li.selected { background-color: #e9ecef; border-color: #ccc; font-weight: bold; }
.module-card { margin-bottom: 1.5rem; }
.content-list { list-style: none; padding-left: 1rem; margin-top: 1rem; }
.content-item { background-color: #f8f9fa; padding: 0.5rem; border-radius: 4px; margin-bottom: 0.5rem; }
.add-content-form { margin-top: 1.5rem; padding-top: 1rem; border-top: 1px solid #eee; }
.add-content-form > input, .add-content-form > select, .add-content-form > textarea { margin-bottom: 1rem; }
.quiz-builder { border: 1px solid #e9ecef; padding: 1rem; margin-top: 1rem; border-radius: 5px; background: #f8f9fa; }
.new-question-form { margin-top: 1rem; padding-top: 1rem; border-top: 1px dashed #ccc; }
.new-question-form h5 { margin-top: 0; }
.new-question-form input[type="text"] { margin-bottom: 0.5rem; }
.correct-answer-selector { font-size: 0.9em; margin: 0.5rem 0; display: flex; align-items: center; gap: 1rem; }
.correct-answer-selector label { display: flex; align-items: center; gap: 0.25rem; }
.btn-add-q { background-color: #28a745; color: white; border: none; padding: 0.5rem 1rem; border-radius: 4px; cursor: pointer; }
.question-preview { display: flex; justify-content: space-between; align-items: center; background: #fff; padding: 0.5rem; border-radius: 4px; margin-bottom: 0.5rem; }
.btn-remove-q { background-color: #dc3545; color: white; border: none; border-radius: 50%; width: 20px; height: 20px; cursor: pointer; line-height: 20px; text-align: center; }
.btn-small { padding: 0.5rem 1rem; }
.btn-secondary { display: inline-block; background-color: #6c757d; margin-bottom: 1.5rem; text-decoration: none; padding: .5rem 1rem; color: white; border-radius: 4px; font-size: .9rem;}
.course-mgmt-container { max-width: 1200px; margin: 2rem auto; padding: 1rem; }
.card { background: #fff; padding: 1.5rem; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
.form-group { margin-bottom: 1rem; }
label { display: block; margin-bottom: 0.5rem; font-weight: 500; }
input, textarea, select { width: 100%; padding: 0.75rem; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; }
.btn { background-color: #007bff; color: white; padding: 0.75rem 1.5rem; border: none; border-radius: 4px; cursor: pointer; }
.message { padding: 1rem; border-radius: 4px; text-align: center; position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%); z-index: 100;}
.success { background-color: #d4edda; color: #155724; }
.error { background-color: #f8d7da; color: #721c24; }
</style>