<template>
  <div class="chatbot-wrapper" v-if="authStore.isStudent">
    <!-- Chat Toggle Button -->
    <button class="chat-toggle" @click="isOpen = !isOpen" :class="{ 'chat-open': isOpen }">
      <span v-if="!isOpen" class="chat-icon">&#x1F4AC;</span>
      <span v-else class="chat-icon">&times;</span>
    </button>

    <!-- Chat Panel -->
    <transition name="slide-up">
      <div v-if="isOpen" class="chat-panel">
        <div class="chat-header">
          <h3>StudyBot</h3>
          <span class="chat-subtitle">AI Tutor</span>
        </div>

        <div class="chat-messages" ref="messagesContainer">
          <div v-if="messages.length === 0" class="chat-welcome">
            <p>Hi! I'm <strong>StudyBot</strong>. Open a course article and click <strong>"Ask StudyBot"</strong> to ask me questions about it!</p>
          </div>
          <div v-for="(msg, idx) in messages" :key="idx" class="message" :class="msg.role">
            <div class="msg-bubble">{{ msg.content }}</div>
          </div>
          <div v-if="isTyping" class="message bot">
            <div class="msg-bubble typing-indicator">
              <span></span><span></span><span></span>
            </div>
          </div>
        </div>

        <div class="chat-input-area">
          <textarea v-model="userInput" @keydown.enter.prevent="sendMessage" placeholder="Ask a question..." rows="1"></textarea>
          <button @click="sendMessage" :disabled="!userInput.trim() || isTyping" class="send-btn">
            &#x27A4;
          </button>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue';
import { useAuthStore } from '@/stores/auth';
import apiClient from '@/api';

const authStore = useAuthStore();

const isOpen = ref(false);
const messages = ref([]);
const userInput = ref('');
const isTyping = ref(false);
const articleContext = ref('');
const messagesContainer = ref(null);

const setContext = (text) => {
  articleContext.value = text;
  isOpen.value = true;
  messages.value.push({
    role: 'bot',
    content: 'Article loaded! Ask me anything about it.'
  });
};

const scrollToBottom = async () => {
  await nextTick();
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
  }
};

const sendMessage = async () => {
  const question = userInput.value.trim();
  if (!question) return;

  messages.value.push({ role: 'user', content: question });
  userInput.value = '';
  isTyping.value = true;
  scrollToBottom();

  try {
    const response = await apiClient.post('/ai/chatbot', {
      question: question,
      context: articleContext.value || 'No specific article loaded. Please help with general study questions.'
    });
    messages.value.push({ role: 'bot', content: response.data.answer });
  } catch (err) {
    messages.value.push({ role: 'bot', content: 'Sorry, I encountered an error. Please try again.' });
  } finally {
    isTyping.value = false;
    scrollToBottom();
  }
};

defineExpose({ setContext });
</script>

<style scoped>
.chatbot-wrapper { position: fixed; bottom: 1.5rem; right: 1.5rem; z-index: 1000; }

.chat-toggle { width: 56px; height: 56px; border-radius: 50%; border: none; background: linear-gradient(135deg, #667eea, #764ba2); color: white; font-size: 1.5rem; cursor: pointer; box-shadow: 0 4px 16px rgba(102, 126, 234, 0.4); transition: transform 0.2s, box-shadow 0.2s; display: flex; align-items: center; justify-content: center; }
.chat-toggle:hover { transform: scale(1.1); box-shadow: 0 6px 20px rgba(102, 126, 234, 0.5); }
.chat-toggle.chat-open { background: #dc3545; }

.chat-panel { position: absolute; bottom: 70px; right: 0; width: 360px; height: 480px; background: white; border-radius: 12px; box-shadow: 0 8px 32px rgba(0,0,0,0.15); display: flex; flex-direction: column; overflow: hidden; }

.chat-header { background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 1rem; display: flex; align-items: center; gap: 0.75rem; }
.chat-header h3 { margin: 0; font-size: 1.1rem; }
.chat-subtitle { font-size: 0.8rem; opacity: 0.8; }

.chat-messages { flex: 1; overflow-y: auto; padding: 1rem; display: flex; flex-direction: column; gap: 0.75rem; }
.chat-welcome { color: #6c757d; font-size: 0.9rem; text-align: center; margin-top: 2rem; }

.message { display: flex; }
.message.user { justify-content: flex-end; }
.message.bot { justify-content: flex-start; }
.msg-bubble { max-width: 80%; padding: 0.6rem 1rem; border-radius: 12px; font-size: 0.9rem; line-height: 1.4; word-wrap: break-word; }
.message.user .msg-bubble { background: #667eea; color: white; border-bottom-right-radius: 4px; }
.message.bot .msg-bubble { background: #f0f2f5; color: #333; border-bottom-left-radius: 4px; }

/* Typing animation */
.typing-indicator { display: flex; gap: 4px; padding: 0.8rem 1.2rem !important; }
.typing-indicator span { width: 8px; height: 8px; border-radius: 50%; background: #999; animation: bounce 1.2s infinite ease-in-out; }
.typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
.typing-indicator span:nth-child(3) { animation-delay: 0.4s; }
@keyframes bounce { 0%, 60%, 100% { transform: translateY(0); } 30% { transform: translateY(-6px); } }

.chat-input-area { border-top: 1px solid #eee; padding: 0.75rem; display: flex; gap: 0.5rem; }
.chat-input-area textarea { flex: 1; border: 1px solid #ddd; border-radius: 20px; padding: 0.5rem 1rem; resize: none; font-size: 0.9rem; outline: none; }
.chat-input-area textarea:focus { border-color: #667eea; }
.send-btn { border: none; background: #667eea; color: white; width: 36px; height: 36px; border-radius: 50%; cursor: pointer; font-size: 1rem; display: flex; align-items: center; justify-content: center; }
.send-btn:disabled { opacity: 0.5; cursor: not-allowed; }

/* Slide up animation */
.slide-up-enter-active, .slide-up-leave-active { transition: all 0.3s ease; }
.slide-up-enter-from, .slide-up-leave-to { transform: translateY(20px); opacity: 0; }

@media (max-width: 480px) {
  .chat-panel { width: calc(100vw - 2rem); right: -0.5rem; }
}
</style>