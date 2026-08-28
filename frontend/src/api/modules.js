import api from './index'

export const authApi = {
  login: (data) => api.post('/auth/login', data),
  register: (data) => api.post('/auth/register', data),
  adminLogin: (data) => api.post('/auth/admin/login', data),
  sendSms: (data) => api.post('/auth/send-sms', data),
  loginBySms: (data) => api.post('/auth/login-by-sms', data),
  registerBySms: (data) => api.post('/auth/register-by-sms', data),
  resetPassword: (data) => api.post('/auth/reset-password', data),
}

export const userApi = {
  getMe: () => api.get('/user/me'),
  updateMe: (params) => api.put('/user/me', null, { params }),
}

export const productApi = {
  getCategories: () => api.get('/products/categories'),
  getProducts: (params) => api.get('/products', { params }),
  getMyProducts: (params) => api.get('/products/my', { params }),
  getProduct: (id) => api.get(`/products/${id}`),
  createProduct: (data) => api.post('/products', data),
  updateProduct: (id, data) => api.put(`/products/${id}`, data),
  favorite: (id) => api.post(`/products/${id}/favorite`),
  getFavorites: (params) => api.get('/products/favorites', { params }),
}

export const orderApi = {
  getCart: () => api.get('/orders/cart'),
  addToCart: (data) => api.post('/orders/cart', data),
  updateCart: (id, qty) => api.put(`/orders/cart/${id}`, null, { params: { qty } }),
  removeCart: (id) => api.delete(`/orders/cart/${id}`),
  clearCart: () => api.delete('/orders/cart'),
  createOrder: (data) => api.post('/orders', data),
  createCourseOrder: (courseId) => api.post('/orders/course', { course_id: courseId }),
  getOrders: (params) => api.get('/orders', { params }),
  getOrder: (id) => api.get(`/orders/${id}`),
  cancelOrder: (id) => api.post(`/orders/${id}/cancel`),
  payOrder: (id, method) => api.post(`/orders/${id}/pay`, null, { params: { pay_method: method } }),
  completeOrder: (id) => api.post(`/orders/${id}/complete`),
  getAddresses: () => api.get('/orders/addresses'),
  createAddress: (data) => api.post('/orders/addresses', data),
  updateAddress: (id, data) => api.put(`/orders/addresses/${id}`, data),
  deleteAddress: (id) => api.delete(`/orders/addresses/${id}`),
}

export const paymentApi = {
  createAlipayPayment: (orderId) => api.get(`/payment/pay/${orderId}`),
  queryPaymentStatus: (orderId) => api.get(`/payment/query/${orderId}`),
  // 公开接口，无需登录，供支付宝回调页使用
  queryStatusByNo: (orderNo) => api.get(`/payment/status-by-no/${orderNo}`),
  // 定制订单支付
  createCustomAlipayPayment: (orderId) => api.get(`/payment/custom-pay/${orderId}`),
  queryCustomPaymentStatus: (orderId) => api.get(`/payment/custom-query/${orderId}`),
  // 课程支付
  createCourseAlipayPayment: (courseId) => api.get(`/payment/course-pay/${courseId}`),
  // 支付倒计时
  getPaymentRemainingTime: (orderId) => api.get(`/payment/remaining-time/${orderId}`),
  getCustomPaymentRemainingTime: (orderId) => api.get(`/payment/custom-remaining-time/${orderId}`),
}

export const artisanApi = {
  apply: (data) => api.post('/artisan/apply', data),
  getMy: () => api.get('/artisan/my'),
  updateMy: (data) => api.put('/artisan/my', data),
  getArtisan: (id) => api.get(`/artisan/${id}`),
  follow: (id) => api.post(`/artisan/${id}/follow`),
  getCustomOrders: (params) => api.get('/artisan/custom', { params }),
  createCustomOrder: (data) => api.post('/artisan/custom', data),
  getCustomOrder: (id) => api.get(`/artisan/custom/${id}`),
  quoteCustomOrder: (id, data) => api.post(`/artisan/custom/${id}/quote`, data),
  acceptCustomOrder: (id) => api.post(`/artisan/custom/${id}/accept`),
  rejectCustomOrder: (id, reason) => api.post(`/artisan/custom/${id}/reject`, null, { params: { reason } }),
  cancelCustomOrder: (id) => api.post(`/artisan/custom/${id}/cancel`),
  shipCustomOrder: (id) => api.post(`/artisan/custom/${id}/ship`),
  completeCustomOrder: (id) => api.post(`/artisan/custom/${id}/complete`),
  updateCustomAddress: (id, data) => api.post(`/artisan/custom/${id}/address`, data),
  updateCustomProgress: (id, progress) => api.post(`/artisan/custom/${id}/progress`, null, { params: { progress } }),
  getCustomMessages: (id) => api.get(`/artisan/custom/${id}/messages`),
  sendCustomMessage: (id, data) => api.post(`/artisan/custom/${id}/messages`, data),
  getOrders: (params) => api.get('/orders/artisan', { params }),
  getDashboard: (params) => api.get('/artisan/dashboard', { params }),
  shipOrder: (id) => api.post(`/orders/artisan/${id}/ship`),
  getTransactions: (params) => api.get('/artisan/transactions', { params }),
}

export const forumApi = {
  // 帖子
  getPosts: (params) => api.get('/forum', { params }),
  getPost: (id) => api.get(`/forum/${id}`),
  createPost: (data) => api.post('/forum', data),
  updatePost: (id, data) => api.put(`/forum/${id}`, data),
  deletePost: (id) => api.delete(`/forum/${id}`),
  // 用户信息
  getUserProfile: (id) => api.get(`/forum/users/${id}`),
  // 互动
  likePost: (id) => api.post(`/forum/${id}/like`),
  favoritePost: (id) => api.post(`/forum/${id}/favorite`),
  // 评论
  getComments: (id, params) => api.get(`/forum/${id}/comments`, { params }),
  createComment: (id, data) => api.post(`/forum/${id}/comments`, data),
  // 关注
  followUser: (id) => api.post(`/forum/users/${id}/follow`),
  getFollowers: (id, params) => api.get(`/forum/users/${id}/followers`, { params }),
  getFollowing: (id, params) => api.get(`/forum/users/${id}/following`, { params }),
  // 收藏
  getFavorites: (params) => api.get('/forum/favorites', { params }),
  // 通知
  getNotifications: (params) => api.get('/forum/notifications', { params }),
  getUnreadCount: () => api.get('/forum/notifications/unread-count'),
  markNotificationRead: (id) => api.post(`/forum/notifications/${id}/read`),
  markAllNotificationsRead: () => api.post('/forum/notifications/read-all'),
  // 草稿
  getDrafts: (params) => api.get('/forum', { params: { ...params, status: 'draft' } }),
  // 论坛浏览记录
  recordForumBrowse: (id) => api.post(`/forum/posts/${id}/browse`),
  getForumBrowseHistory: (params) => api.get('/forum/browse-history', { params }),
  deleteForumBrowse: (id) => api.delete(`/forum/browse-history/${id}`),
  clearForumBrowseHistory: () => api.delete('/forum/browse-history'),
}

export const adminApi = {
  getStats: () => api.get('/orders/admin/stats'),
  getAllOrders: (params) => api.get('/orders/admin/all', { params }),
  shipOrder: (id) => api.post(`/orders/admin/${id}/ship`),
  getArtisanApplications: (params) => api.get('/artisan/admin/applications', { params }),
  approveArtisan: (id) => api.post(`/artisan/admin/${id}/approve`),
  rejectArtisan: (id, reason) => api.post(`/artisan/admin/${id}/reject`, null, { params: { reason } }),
  getPendingProducts: (params) => api.get('/products/pending', { params }),
  approveProduct: (id) => api.post(`/products/${id}/approve`),
  rejectProduct: (id, reason) => api.post(`/products/${id}/reject`, null, { params: { reason } }),
  createCategory: (data) => api.post('/products/categories', data),
  updateCategory: (id, params) => api.put(`/products/categories/${id}`, null, { params }),
  deleteCategory: (id) => api.delete(`/products/categories/${id}`),
  deleteForumPost: (id) => api.delete(`/forum/${id}`),
  getForumPosts: (params) => api.get('/forum/admin/posts', { params }),
  approveForumPost: (id) => api.post(`/forum/admin/posts/${id}/approve`),
  rejectForumPost: (id, reason) => api.post(`/forum/admin/posts/${id}/reject`, null, { params: { reason } }),
}

export const courseApi = {
  // Public
  getCourses: (params) => api.get('/courses', { params }),
  getCourse: (id) => api.get(`/courses/${id}`),
  // 搜索建议（自动补全）
  suggestCourses: (params) => api.get('/courses/suggest', { params }),
  // Admin
  getAdminCourses: (params) => api.get('/courses/admin/pending', { params }),
  getAdminCourseDetail: (id) => api.get(`/courses/admin/${id}/detail`),
  approveCourse: (id) => api.post(`/courses/admin/${id}/approve`),
  rejectCourse: (id, reason) => api.post(`/courses/admin/${id}/reject`, null, { params: { reason } }),
  // User
  enroll: (id) => api.post(`/courses/${id}/enroll`),
  dropCourse: (id) => api.post(`/courses/${id}/drop`),
  getEnrollment: (id) => api.get(`/courses/${id}/enrollment`),
  learnCourse: (id) => api.get(`/courses/${id}/learn`),
  updateProgress: (id, data) => api.post(`/courses/${id}/progress`, data),
  getMyEnrollments: (params) => api.get('/courses/enrollments', { params }),
  // My Courses (user side)
  getMyCourses: (params) => api.get('/courses/my-courses', { params }),
  // Browse History
  recordBrowse: (id, lessonId) => api.post(`/courses/browse/${id}`, null, { params: lessonId ? { lesson_id: lessonId } : {} }),
  getBrowseHistory: (params) => api.get('/courses/browse-history', { params }),
  recordProductBrowse: (id) => api.post(`/products/${id}/browse`),
  deleteBrowseHistory: (id) => api.delete(`/courses/browse-history/${id}`),
  clearBrowseHistory: () => api.delete('/courses/browse-history'),
  // Comments
  getComments: (id) => api.get(`/courses/${id}/comments`),
  createComment: (id, data) => api.post(`/courses/${id}/comments`, data),
  // Study Notes
  getNotes: (id) => api.get(`/courses/${id}/notes`),
  createNote: (id, data) => api.post(`/courses/${id}/notes`, data),
  updateNote: (id, data) => api.put(`/courses/notes/${id}`, data),
  deleteNote: (id) => api.delete(`/courses/notes/${id}`),
  // Artisan management
  getArtisanCourses: (params) => api.get('/courses/manage', { params }),
  createCourse: (data) => api.post('/courses', data),
  updateCourse: (id, data) => api.put(`/courses/${id}`, data),
  deleteCourse: (id) => api.delete(`/courses/${id}`),
  // Chapters
  addChapter: (courseId, data) => api.post(`/courses/${courseId}/chapters`, data),
  updateChapter: (courseId, chapterId, data) => api.put(`/courses/${courseId}/chapters/${chapterId}`, data),
  deleteChapter: (courseId, chapterId) => api.delete(`/courses/${courseId}/chapters/${chapterId}`),
  // Lessons
  addLesson: (courseId, chapterId, data) => api.post(`/courses/${courseId}/chapters/${chapterId}/lessons`, data),
  updateLesson: (courseId, lessonId, data) => api.put(`/courses/${courseId}/lessons/${lessonId}`, data),
  deleteLesson: (courseId, lessonId) => api.delete(`/courses/${courseId}/lessons/${lessonId}`),
  // Upload helpers
  uploadVideo: (file) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/upload/video', formData, { headers: { 'Content-Type': 'multipart/form-data' }, timeout: 600000 })
  },
  uploadImage: (file) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/upload/image', formData, { headers: { 'Content-Type': 'multipart/form-data' } })
  },
  // 课程评论通知
  getNotifications: (params) => api.get('/courses/notifications', { params }),
  getUnreadCount: () => api.get('/courses/notifications/unread-count'),
}

export const workflowApi = {
  // 生成/润色文案: content_type, title, user_input
  // 返回: { result, tech_intro }
  // LangGraph 工作流含多轮 LLM 调用, timeout 设为 130s (后端 120s + 余量)
  generateCopy: (content_type, title, user_input = '') =>
    api.post('/workflow/generate', { content_type, title, user_input }, { timeout: 130000 }),
}

export const chatApi = {
  // 发送消息到非遗百晓生 AI 问答, 返回 SSE 流
  // 会话记忆: 后端内存版, 传 conversation_id 时支持会话内多轮追问,
  // 前端「新对话」生成新 ID 即开启全新上下文; 传空则单轮独立问答
  // 返回 fetch Response (ReadableStream)
  sendMessage: (query, conversation_id = '') => {
    const token = localStorage.getItem('token')
    return fetch('/api/chat/messages', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({ query, conversation_id }),
    })
  },
}

export const searchApi = {
  // 全文检索
  searchProducts: (params) => api.get('/search/products', { params }),
  // 搜索建议
  suggest: (params) => api.get('/search/suggest', { params }),
  // 索引管理
  createIndex: () => api.post('/search/index/create'),
  rebuildIndex: () => api.post('/search/index/rebuild'),
  // 数据同步
  syncProduct: (id) => api.post(`/search/sync/product/${id}`),
  deleteProduct: (id) => api.delete(`/search/sync/product/${id}`),
}
