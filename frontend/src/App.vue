<template>
  <div class="app">
    <el-container>
      <el-header class="header">
        <div class="header-content">
          <el-icon class="logo-icon">
            <Food />
          </el-icon>
          <h1>尝尝咸淡</h1>
          <span class="subtitle">智能食谱助手</span>
        </div>
      </el-header>

      <el-main class="main">
        <div class="content-wrapper">
          <div class="chat-container">
            <div
              class="chat-messages"
              ref="messagesContainer"
            >
              <div
                v-for="(message, index) in messages"
                :key="index"
                :class="['message', message.role]"
              >
                <div class="message-content">
                  <div
                    v-if="message.role === 'assistant'"
                    class="avatar assistant"
                  >
                    <el-icon>
                      <Food />
                    </el-icon>
                  </div>
                  <div
                    v-else
                    class="avatar user"
                  >
                    <el-icon>
                      <User />
                    </el-icon>
                  </div>
                  <div class="message-text">
                    <div v-html="formatMessage(message.content)"></div>
                    <img
                      v-if="message.image"
                      :src="message.image"
                      class="message-image"
                      alt="上传的图片"
                    />
                    <div
                      v-if="message.documents && message.documents.length > 0"
                      class="related-docs"
                    >
                      <el-tag
                        v-for="(doc, idx) in message.documents"
                        :key="idx"
                        size="small"
                        type="info"
                        class="doc-tag"
                      >
                        {{ doc.dish_name }}
                        <span class="doc-meta">({{ doc.category }} ·
                          {{ doc.difficulty }})</span>
                      </el-tag>
                    </div>
                  </div>
                </div>
              </div>
              <div
                v-if="loading"
                class="message assistant"
              >
                <div class="message-content">
                  <div class="avatar assistant">
                    <el-icon>
                      <Food />
                    </el-icon>
                  </div>
                  <div class="message-text loading">
                    <el-icon class="is-loading">
                      <Loading />
                    </el-icon>
                    <span>正在思考中...</span>
                  </div>
                </div>
              </div>
            </div>

            <div class="chat-input">
              <div class="input-actions">
                <el-upload
                  ref="uploadRef"
                  :auto-upload="false"
                  :show-file-list="false"
                  :on-change="handleImageSelect"
                  accept="image/*"
                  :limit="1"
                >
                  <el-button
                    :icon="Picture"
                    circle
                    class="upload-button"
                  />
                </el-upload>
              </div>
              <div class="input-main">
                <div
                  v-if="previewImage"
                  class="image-preview"
                >
                  <img
                    :src="previewImage"
                    alt="预览图片"
                  />
                  <el-button
                    :icon="Close"
                    circle
                    size="small"
                    class="preview-close"
                    @click="removePreview"
                  />
                </div>
                <el-input
                  v-model="inputMessage"
                  type="textarea"
                  :rows="2"
                  placeholder="问我任何关于食谱的问题，比如：宫保鸡丁怎么做？"
                  @keydown.enter.prevent="handleEnter"
                  :disabled="loading"
                />
              </div>
              <el-button
                type="primary"
                :icon="Promotion"
                @click="sendMessage"
                :loading="loading"
                :disabled="!inputMessage.trim() && !selectedImage"
                class="send-button"
              >
                发送
              </el-button>
            </div>
          </div>

          <div class="sidebar">
            <el-card class="stats-card">
              <template #header>
                <div class="card-header">
                  <el-icon>
                    <DataAnalysis />
                  </el-icon>
                  <span>知识库统计</span>
                </div>
              </template>
              <div
                v-if="stats"
                class="stats-content"
              >
                <div class="stat-item">
                  <span class="stat-label">食谱总数</span>
                  <span class="stat-value">{{ stats.total_documents }}</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">文本块数</span>
                  <span class="stat-value">{{ stats.total_chunks }}</span>
                </div>
                <div class="stat-divider"></div>
                <div class="stat-section">
                  <span class="stat-section-title">菜品分类</span>
                  <div class="category-list">
                    <div
                      v-for="(count, category) in stats.categories"
                      :key="category"
                      class="category-item"
                    >
                      <span>{{ category }}</span>
                      <el-tag size="small">{{ count }}</el-tag>
                    </div>
                  </div>
                </div>
              </div>
              <div
                v-else
                class="loading-stats"
              >
                <el-icon class="is-loading">
                  <Loading />
                </el-icon>
                <span>加载中...</span>
              </div>
            </el-card>

            <el-card class="quick-actions-card">
              <template #header>
                <div class="card-header">
                  <el-icon>
                    <Lightning />
                  </el-icon>
                  <span>快捷操作</span>
                </div>
              </template>
              <div class="quick-actions">
                <el-button
                  v-for="action in quickActions"
                  :key="action.text"
                  :type="action.type"
                  :icon="action.icon"
                  size="small"
                  @click="inputMessage = action.text"
                  class="action-button"
                >
                  {{ action.text }}
                </el-button>
              </div>
            </el-card>
          </div>
        </div>
      </el-main>
    </el-container>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Food, User, Promotion, Loading,
  DataAnalysis, Lightning, ChatDotRound,
  Star, Coffee, Dessert, Picture, Close
} from '@element-plus/icons-vue'
import axios from 'axios'
import { marked } from 'marked'

const messages = ref([
  {
    role: 'assistant',
    content: '你好！我是尝尝咸淡智能食谱助手。我可以帮你：\n\n• 推荐菜品和食谱\n• 提供详细的制作步骤\n• 解答烹饪问题\n• 按分类或难度筛选菜品\n\n有什么我可以帮你的吗？'
  }
])
const inputMessage = ref('')
const loading = ref(false)
const messagesContainer = ref(null)
const stats = ref(null)
const selectedImage = ref(null)
const uploadRef = ref(null)
const previewImage = ref(null)
const uploadedImageName = ref('')

const quickActions = [
  { text: '推荐几个素菜', icon: ChatDotRound, type: 'success' },
  { text: '简单的早餐推荐', icon: Coffee, type: 'warning' },
  { text: '有什么甜品', icon: Dessert, type: 'danger' },
  { text: '川菜推荐', icon: Star, type: 'primary' }
]

const formatMessage = (content) => {
  if (!content) return ''
  return marked.parse(content)
}

const scrollToBottom = async () => {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

const handleEnter = (e) => {
  if (!e.shiftKey) {
    e.preventDefault()
    sendMessage()
  }
}

const handleImageSelect = (file) => {
  selectedImage.value = file.raw
  previewImage.value = URL.createObjectURL(file.raw)
  ElMessage.success('图片已选择，请输入问题或直接发送')
}

const removePreview = () => {
  if (previewImage.value) {
    URL.revokeObjectURL(previewImage.value)
  }
  selectedImage.value = null
  uploadedImageName.value = ''
  previewImage.value = null
  if (uploadRef.value) {
    uploadRef.value.clearFiles()
  }
}

const resetUpload = () => {
  removePreview()
}

const sendMessage = async () => {
  const message = inputMessage.value.trim()
  if (!message && !selectedImage.value || loading.value) return

  let imageUrl = null
  let imageName = null

  if (selectedImage.value) {
    const formData = new FormData()
    formData.append('file', selectedImage.value)

    try {
      const uploadResponse = await axios.post('/api/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })

      if (uploadResponse.data.success) {
        imageUrl = uploadResponse.data.url
        imageName = uploadResponse.data.filename
        uploadedImageName.value = imageName
        ElMessage.success('图片上传成功')
      }
    } catch (error) {
      console.error('图片上传失败:', error)
      ElMessage.error('图片上传失败，请重试')
      resetUpload()
      return
    }
  }

  if (message) {
    messages.value.push({
      role: 'user',
      content: message,
      image: imageUrl
    })
  } else if (imageUrl) {
    messages.value.push({
      role: 'user',
      content: '',
      image: imageUrl
    })
  }

  inputMessage.value = ''
  resetUpload()
  loading.value = true
  await scrollToBottom()

  try {
    const response = await fetch('/api/ask_stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        question: message,
        image_name: imageName
      })
    })

    if (!response.ok) {
      throw new Error('Network response was not ok')
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()

    let assistantMessage = {
      role: 'assistant',
      content: '',
      documents: [],
      route_type: ''
    }

    messages.value.push(assistantMessage)
    const messageIndex = messages.value.length - 1

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      const chunk = decoder.decode(value)
      const lines = chunk.split('\n')

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6))

            if (data.answer) {
              messages.value[messageIndex].content += data.answer
            }

            if (data.route_type) {
              messages.value[messageIndex].route_type = data.route_type
            }

            if (data.documents && data.documents.length > 0) {
              messages.value[messageIndex].documents = data.documents
            }

            await scrollToBottom()
          } catch (e) {
            console.error('Error parsing SSE data:', e)
          }
        }
      }
    }
  } catch (error) {
    console.error('Error:', error)
    ElMessage.error('抱歉，出现了一些问题，请稍后再试')
    messages.value.push({
      role: 'assistant',
      content: '抱歉，出现了一些问题，请稍后再试。'
    })
  } finally {
    loading.value = false
    await scrollToBottom()
  }
}

const fetchStats = async () => {
  try {
    const response = await axios.get('/api/stats')
    stats.value = response.data.data
  } catch (error) {
    console.error('Failed to fetch stats:', error)
  }
}

onMounted(() => {
  fetchStats()
})
</script>

<style scoped>
.app {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.header {
  background: rgba(255, 255, 255, 0.95);
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  display: flex;
  align-items: center;
  padding: 0 40px;
}

.header-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.logo-icon {
  font-size: 32px;
  color: #667eea;
}

.header h1 {
  margin: 0;
  font-size: 24px;
  color: #333;
}

.subtitle {
  color: #999;
  font-size: 14px;
}

.main {
  padding: 40px;
}

.content-wrapper {
  display: flex;
  gap: 24px;
  max-width: 1400px;
  margin: 0 auto;
  height: calc(100vh - 140px);
}

.chat-container {
  flex: 1;
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  background: #f5f7fa;
}

.message {
  margin-bottom: 20px;
  animation: slideIn 0.3s ease;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.message-content {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  flex-shrink: 0;
}

.avatar.assistant {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.avatar.user {
  background: #409eff;
  color: white;
}

.message.user .message-content {
  flex-direction: row-reverse;
}

.message-text {
  background: white;
  padding: 16px 20px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  max-width: 70%;
  line-height: 1.6;
}

.message.user .message-text {
  background: #409eff;
  color: white;
}

.message-text h3 {
  margin: 12px 0 8px 0;
  font-size: 16px;
  color: #333;
}

.message-text h4 {
  margin: 8px 0 4px 0;
  font-size: 14px;
  color: #666;
}

.message-text :deep(h1),
.message-text :deep(h2),
.message-text :deep(h3),
.message-text :deep(h4) {
  margin-top: 12px;
  margin-bottom: 8px;
  font-weight: 600;
  line-height: 1.4;
}

.message-text :deep(h1) {
  font-size: 18px;
  color: #333;
}

.message-text :deep(h2) {
  font-size: 16px;
  color: #333;
}

.message-text :deep(h3) {
  font-size: 15px;
  color: #666;
}

.message-text :deep(h4) {
  font-size: 14px;
  color: #666;
}

.message-text :deep(p) {
  margin: 8px 0;
  line-height: 1.6;
}

.message-text :deep(ul),
.message-text :deep(ol) {
  margin: 8px 0;
  padding-left: 20px;
}

.message-text :deep(li) {
  margin: 4px 0;
  line-height: 1.6;
}

.message-text :deep(strong) {
  font-weight: 600;
  color: #333;
}

.message-text :deep(em) {
  font-style: italic;
}

.message-text :deep(code) {
  background: #f5f5f5;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: "Courier New", monospace;
  font-size: 13px;
  color: #e83e8c;
}

.message-text :deep(pre) {
  background: #f5f5f5;
  padding: 12px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 8px 0;
}

.message-text :deep(pre code) {
  background: none;
  padding: 0;
  color: #333;
}

.message-text :deep(blockquote) {
  border-left: 4px solid #667eea;
  padding-left: 12px;
  margin: 8px 0;
  color: #666;
  font-style: italic;
}

.message-text :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 8px 0;
}

.message-text :deep(th),
.message-text :deep(td) {
  border: 1px solid #eee;
  padding: 8px 12px;
  text-align: left;
}

.message-text :deep(th) {
  background: #f5f5f5;
  font-weight: 600;
}

.message-text :deep(hr) {
  border: none;
  border-top: 1px solid #eee;
  margin: 12px 0;
}

.message-text li {
  margin-left: 20px;
  margin-bottom: 4px;
}

.message-image {
  max-width: 100%;
  max-height: 300px;
  border-radius: 8px;
  margin-top: 12px;
  object-fit: contain;
}

.message-text.loading {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #999;
}

.related-docs {
  margin-top: 12px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.doc-tag {
  margin: 0;
}

.doc-meta {
  margin-left: 4px;
  opacity: 0.7;
}

.chat-input {
  padding: 20px;
  background: white;
  border-top: 1px solid #eee;
  display: flex;
  gap: 12px;
  align-items: flex-end;
}

.input-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.upload-button {
  width: 40px;
  height: 40px;
  flex-shrink: 0;
}

.input-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.image-preview {
  position: relative;
  display: inline-block;
  max-width: 200px;
}

.image-preview img {
  max-width: 100%;
  max-height: 150px;
  border-radius: 8px;
  object-fit: contain;
  border: 2px solid #e0e0e0;
}

.preview-close {
  position: absolute;
  top: -8px;
  right: -8px;
  background: white;
  border: 2px solid #ff4d4f;
  color: #ff4d4f;
  width: 24px;
  height: 24px;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s;
}

.preview-close:hover {
  background: #ff4d4f;
  color: white;
}

.chat-input :deep(.el-textarea__inner) {
  border-radius: 8px;
  resize: none;
}

.send-button {
  height: 56px;
  padding: 0 32px;
  font-size: 16px;
}

.sidebar {
  width: 320px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.stats-card,
.quick-actions-card {
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
}

.stats-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stat-label {
  color: #666;
  font-size: 14px;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  color: #667eea;
}

.stat-divider {
  height: 1px;
  background: #eee;
}

.stat-section-title {
  font-weight: 600;
  color: #333;
  margin-bottom: 12px;
  display: block;
}

.category-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.category-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 14px;
}

.loading-stats {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 20px;
  color: #999;
}

.quick-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.action-button {
  width: 100%;
  justify-content: flex-start;
}

@media (max-width: 1024px) {
  .content-wrapper {
    flex-direction: column;
    height: auto;
  }

  .sidebar {
    width: 100%;
  }

  .header {
    padding: 0 20px;
  }

  .main {
    padding: 20px;
  }
}
</style>
