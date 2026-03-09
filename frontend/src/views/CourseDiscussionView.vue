<template>
  <div class="discussion-container">
    <div class="discussion-header">
      <RouterLink :to="{ name: 'course-details', params: { courseId: courseId } }" class="btn-back">&larr; Back to Course</RouterLink>
      <h1>Discussion Board</h1>
    </div>

    <!-- New Post Form -->
    <div class="new-post-card" v-if="!activePost">
      <h2>Start a New Discussion</h2>
      <input v-model="newPost.title" type="text" placeholder="Question or topic title..." class="post-title-input" />
      <textarea v-model="newPost.body" placeholder="Describe your question or topic in detail..." rows="4"></textarea>
      <button @click="createPost" class="btn btn-primary" :disabled="!newPost.title.trim() || !newPost.body.trim()">
        Post Discussion
      </button>
    </div>

    <!-- Discussion List -->
    <div v-if="!activePost">
      <div v-if="isLoading" class="loading">Loading discussions...</div>
      <div v-else-if="posts.length === 0" class="empty-state">
        <p>No discussions yet. Be the first to start one!</p>
      </div>
      <div v-else class="posts-list">
        <div v-for="p in posts" :key="p.id" class="post-card" @click="openPost(p.id)">
          <div class="post-info">
            <h3 class="post-title">{{ p.title }}</h3>
            <p class="post-preview">{{ p.body.substring(0, 120) }}{{ p.body.length > 120 ? '...' : '' }}</p>
            <div class="post-meta">
              <span class="author-badge" :class="'role-' + p.author_role.toLowerCase()">{{ p.author_role }}</span>
              <span class="author-name">{{ p.author }}</span>
              <span class="post-date">{{ p.created_at }}</span>
            </div>
          </div>
          <div class="reply-count-badge">
            <span class="count">{{ p.reply_count }}</span>
            <span class="label">{{ p.reply_count === 1 ? 'reply' : 'replies' }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Active Post Detail (Thread View) -->
    <div v-if="activePost" class="thread-view">
      <button @click="activePost = null" class="btn-back">&larr; Back to Discussions</button>

      <div class="thread-post">
        <div class="thread-header">
          <h2>{{ activePost.title }}</h2>
          <div class="post-meta">
            <span class="author-badge" :class="'role-' + activePost.author_role.toLowerCase()">{{ activePost.author_role }}</span>
            <span class="author-name">{{ activePost.author }}</span>
            <span class="post-date">{{ activePost.created_at }}</span>
          </div>
        </div>
        <p class="thread-body">{{ activePost.body }}</p>
      </div>

      <!-- Replies -->
      <div class="replies-section">
        <h3>{{ activePost.replies.length }} {{ activePost.replies.length === 1 ? 'Reply' : 'Replies' }}</h3>
        <div v-for="r in activePost.replies" :key="r.id" class="reply-card" :class="'reply-role-' + r.author_role.toLowerCase()">
          <div class="reply-meta">
            <span class="author-badge" :class="'role-' + r.author_role.toLowerCase()">{{ r.author_role }}</span>
            <span class="author-name">{{ r.author }}</span>
            <span class="post-date">{{ r.created_at }}</span>
          </div>
          <p class="reply-body">{{ r.body }}</p>
        </div>
      </div>

      <!-- Reply Form -->
      <div class="reply-form">
        <textarea v-model="replyBody" placeholder="Write your reply..." rows="3"></textarea>
        <button @click="postReply" class="btn btn-primary" :disabled="!replyBody.trim()">Post Reply</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRoute, RouterLink } from 'vue-router';
import apiClient from '@/api';

const route = useRoute();
const courseId = route.params.courseId;

const posts = ref([]);
const activePost = ref(null);
const isLoading = ref(true);
const newPost = ref({ title: '', body: '' });
const replyBody = ref('');

const fetchPosts = async () => {
  isLoading.value = true;
  try {
    const response = await apiClient.get(`/courses/${courseId}/discussions`);
    posts.value = response.data;
  } catch (err) {
    console.error('Failed to load discussions:', err);
  } finally {
    isLoading.value = false;
  }
};

const createPost = async () => {
  if (!newPost.value.title.trim() || !newPost.value.body.trim()) return;
  try {
    await apiClient.post(`/courses/${courseId}/discussions`, newPost.value);
    newPost.value = { title: '', body: '' };
    await fetchPosts();
  } catch (err) {
    alert(err.response?.data?.error || 'Failed to post discussion.');
  }
};

const openPost = async (postId) => {
  try {
    const response = await apiClient.get(`/discussions/${postId}`);
    activePost.value = response.data;
  } catch (err) {
    alert('Failed to load discussion thread.');
  }
};

const postReply = async () => {
  if (!replyBody.value.trim()) return;
  try {
    await apiClient.post(`/discussions/${activePost.value.id}/replies`, { body: replyBody.value });
    replyBody.value = '';
    // Refresh the thread
    await openPost(activePost.value.id);
  } catch (err) {
    alert(err.response?.data?.error || 'Failed to post reply.');
  }
};

onMounted(fetchPosts);
</script>

<style scoped>
.discussion-container { max-width: 900px; margin: 2rem auto; padding: 1rem; }
.discussion-header { margin-bottom: 1.5rem; }
.discussion-header h1 { margin: 0.5rem 0 0 0; }
.btn-back { display: inline-block; padding: 0.5rem 1rem; background-color: #6c757d; color: white; border-radius: 4px; text-decoration: none; font-weight: bold; border: none; cursor: pointer; font-size: 0.9rem; }

/* New Post Form */
.new-post-card { background: white; padding: 1.5rem; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); margin-bottom: 2rem; }
.new-post-card h2 { margin-top: 0; font-size: 1.1rem; }
.post-title-input { width: 100%; padding: 0.75rem; border: 1px solid #ccc; border-radius: 4px; margin-bottom: 0.75rem; font-size: 1rem; box-sizing: border-box; }
.new-post-card textarea { width: 100%; padding: 0.75rem; border: 1px solid #ccc; border-radius: 4px; resize: vertical; font-size: 0.95rem; box-sizing: border-box; }
.btn { padding: 0.75rem 1.5rem; border: none; border-radius: 4px; cursor: pointer; font-weight: bold; margin-top: 0.75rem; }
.btn:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-primary { background-color: #007bff; color: white; }

/* Post cards */
.posts-list { display: flex; flex-direction: column; gap: 1rem; }
.post-card { background: white; padding: 1.25rem; border-radius: 8px; box-shadow: 0 2px 6px rgba(0,0,0,0.06); cursor: pointer; transition: transform 0.15s, box-shadow 0.15s; display: flex; justify-content: space-between; align-items: center; gap: 1rem; }
.post-card:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
.post-info { flex: 1; }
.post-title { margin: 0 0 0.5rem 0; font-size: 1.1rem; color: #007bff; }
.post-preview { margin: 0 0 0.5rem 0; color: #555; font-size: 0.9rem; }
.post-meta { display: flex; align-items: center; gap: 0.75rem; font-size: 0.8rem; color: #6c757d; flex-wrap: wrap; }

/* Reply count badge */
.reply-count-badge { display: flex; flex-direction: column; align-items: center; background: #f0f7ff; padding: 0.75rem 1rem; border-radius: 8px; flex-shrink: 0; }
.reply-count-badge .count { font-size: 1.3rem; font-weight: bold; color: #007bff; }
.reply-count-badge .label { font-size: 0.7rem; color: #6c757d; text-transform: uppercase; }

/* Author badges */
.author-badge { padding: 0.15rem 0.5rem; border-radius: 10px; font-size: 0.7rem; font-weight: bold; text-transform: uppercase; }
.role-teacher { background: #d4edda; color: #155724; }
.role-student { background: #cce5ff; color: #004085; }
.role-admin { background: #fff3cd; color: #856404; }
.author-name { font-weight: 600; }
.post-date { color: #adb5bd; }

/* Thread view */
.thread-view { margin-top: 1rem; }
.thread-post { background: white; padding: 1.5rem; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); margin: 1rem 0 1.5rem 0; border-left: 4px solid #007bff; }
.thread-header h2 { margin: 0 0 0.5rem 0; }
.thread-body { color: #333; line-height: 1.6; white-space: pre-wrap; }

/* Replies */
.replies-section { margin-bottom: 1.5rem; }
.replies-section h3 { color: #495057; font-size: 1rem; margin-bottom: 1rem; }
.reply-card { background: white; padding: 1rem 1.25rem; border-radius: 6px; margin-bottom: 0.75rem; border: 1px solid #e9ecef; }
.reply-role-teacher { border-left: 3px solid #28a745; background: #f8fff8; }
.reply-role-admin { border-left: 3px solid #ffc107; }
.reply-meta { display: flex; align-items: center; gap: 0.75rem; font-size: 0.8rem; color: #6c757d; margin-bottom: 0.5rem; }
.reply-body { margin: 0; color: #333; line-height: 1.5; white-space: pre-wrap; }

/* Reply form */
.reply-form { background: white; padding: 1.5rem; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
.reply-form textarea { width: 100%; padding: 0.75rem; border: 1px solid #ccc; border-radius: 4px; resize: vertical; box-sizing: border-box; }

.empty-state { text-align: center; color: #6c757d; padding: 3rem; font-style: italic; }
.loading { text-align: center; padding: 3rem; color: #6c757d; }
</style>
