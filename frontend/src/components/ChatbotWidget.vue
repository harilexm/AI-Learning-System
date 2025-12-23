<template>
  <div class="chatbot-container">
    <!-- Chat Bubble (Toggle Button) -->
    <div class="chat-bubble" @click="isOpen = !isOpen">
      🤖
    </div>

    <!-- Chat Window -->
    <div v-if="isOpen" class="chat-window">
      <div class="chat-header">
        <h3>StudyBot</h3>
        <button class="close-btn" @click="isOpen = false">x</button>
      </div>
      <div class="message-area" ref="messageArea">
        <div v-for="(msg, index) in messages" :key="index" class="message" :class="msg.sender">
          {{ msg.text }}
        </div>
        <div v-if="isLoading" class="message bot">...</div>
      </div>
      <div class="input-area">
        <form @submit.prevent="sendMessage">
          <input v-model="userInput" type="text" placeholder="Ask about the article..." :disabled="isLoading" />
          <button type="submit" :disabled="isLoading">Send</button>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue';
import { useAuthStore } from '@/stores/auth';
import apiClient from '@/api';

// Props: The component receives the article text as a 'prop' from its parent
const props = defineProps({
  articleContext: {
    type: String,
    required: true
  }
});

const authStore = useAuthStore();
const isOpen = ref(false);
const userInput = ref('');
const isLoading = ref(false);
const messages = ref([
  { sender: 'bot', text: 'Hello! I am StudyBot. Ask me any questions you have about this article.' }
]);
const messageArea = ref(null); // To control scrolling

const sendMessage = async () => {
  if (!userInput.value.trim()) return;

  const userMessage = userInput.value;
  messages.value.push({ sender: 'user', text: userMessage });
  userInput.value = '';
  isLoading.value = true;

  try {
    const response = await apiClient.post('/ai/chatbot', {
      question: userMessage,
      context: props.articleContext
    });
    
    messages.value.push({ sender: 'bot', text: response.data.answer });
  } catch (err) {
    messages.value.push({ sender: 'bot', text: 'Sorry, I encountered an error. Please try again.' });
  } finally {
    isLoading.value = false;
  }
};

// Auto-scroll to the bottom when new messages are added
watch(messages, async () => {
  await nextTick(); // Wait for the DOM to update
  if (messageArea.value) {
    messageArea.value.scrollTop = messageArea.value.scrollHeight;
  }
}, { deep: true });
</script>

<style scoped>
.chatbot-container {
  position: fixed;
  bottom: 2rem;
  right: 2rem;
  z-index: 1000;
}
.chat-bubble {
  width: 60px;
  height: 60px;
  background-color: #007bff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2rem;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(0,0,0,0.2);
}
.chat-window {
  width: 350px;
  height: 500px;
  background: white;
  border-radius: 10px;
  box-shadow: 0 5px 20px rgba(0,0,0,0.2);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: absolute;
  bottom: 80px;
  right: 0;
}
.chat-header {
  background: #f8f9fa;
  padding: 1rem;
  border-bottom: 1px solid #dee2e6;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.chat-header h3 { margin: 0; }
.close-btn { background: none; border: none; font-size: 1.5rem; cursor: pointer; }
.message-area {
  flex-grow: 1;
  padding: 1rem;
  overflow-y: auto;
}
.message {
  padding: 0.75rem;
  border-radius: 8px;
  margin-bottom: 0.75rem;
  max-width: 80%;
  line-height: 1.4;
}
.message.bot {
  background-color: #e9ecef;
  align-self: flex-start;
}
.message.user {
  background-color: #007bff;
  color: white;
  margin-left: auto;
}
.input-area {
  padding: 1rem;
  border-top: 1px solid #dee2e6;
}
.input-area form {
  display: flex;
}
.input-area input {
  flex-grow: 1;
  border: 1px solid #ccc;
  border-radius: 5px;
  padding: 0.75rem;
}
.input-area button {
  border: none;
  background: #007bff;
  color: white;
  border-radius: 5px;
  padding: 0 1rem;
  margin-left: 0.5rem;
  cursor: pointer;
}
</style>