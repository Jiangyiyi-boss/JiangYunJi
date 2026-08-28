import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'

const routes = [
  {
    path: '/',
    redirect: (to) => {
      const userStore = useUserStore()
      const user = userStore.user
      if (user?.role === 'artisan') {
        return '/artisan/dashboard'
      }
      if (user?.role === 'admin') {
        return '/admin'
      }
      return '/home'
    },
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/LoginView.vue'),
    meta: { guest: true },
  },
  {
    path: '/admin/login',
    name: 'AdminLogin',
    component: () => import('@/views/AdminLoginView.vue'),
    meta: { guest: true },
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/RegisterView.vue'),
    meta: { guest: true },
  },
  {
    path: '/home',
    name: 'Home',
    component: () => import('@/views/HomeView.vue'),
  },
  {
    path: '/search',
    name: 'Search',
    component: () => import('@/views/SearchView.vue'),
  },
  {
    path: '/product/:id',
    name: 'ProductDetail',
    component: () => import('@/views/ProductDetail.vue'),
  },
  {
    path: '/cart',
    name: 'Cart',
    component: () => import('@/views/CartView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/orders',
    name: 'Orders',
    component: () => import('@/views/OrdersView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/pay/:orderId',
    name: 'Pay',
    component: () => import('@/views/PayView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('@/views/ProfileView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/favorites',
    name: 'Favorites',
    component: () => import('@/views/FavoritesView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/addresses',
    name: 'Addresses',
    component: () => import('@/views/AddressesView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/checkout',
    name: 'Checkout',
    component: () => import('@/views/CheckoutView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/pay/callback',
    name: 'PayCallback',
    component: () => import('@/views/PayCallbackView.vue'),
  },
  {
    path: '/forum',
    name: 'Forum',
    component: () => import('@/views/ForumView.vue'),
  },
  {
    path: '/forum/:id',
    name: 'ForumPost',
    component: () => import('@/views/ForumPostView.vue'),
  },
  {
    path: '/artisan/:id',
    name: 'ArtisanShop',
    component: () => import('@/views/ArtisanShopView.vue'),
  },
  {
    path: '/custom',
    name: 'Custom',
    component: () => import('@/views/CustomView.vue'),
  },
  {
    path: '/my',
    name: 'My',
    component: () => import('@/views/MyView.vue'),
  },
  // 商家入驻
  {
    path: '/artisan/apply',
    name: 'ArtisanApply',
    component: () => import('@/views/ArtisanApplyView.vue'),
    meta: { requiresAuth: true },
  },
  // 在线教育
  {
    path: '/courses',
    name: 'Courses',
    component: () => import('@/views/CoursesView.vue'),
  },
  {
    path: '/course/:id',
    name: 'CourseDetail',
    component: () => import('@/views/CourseDetailView.vue'),
  },
  {
    path: '/course-checkout/:courseId',
    name: 'CourseCheckout',
    component: () => import('@/views/CourseCheckoutView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/custom-checkout/:orderId',
    name: 'CustomCheckout',
    component: () => import('@/views/CustomCheckoutView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/course/:id/learn',
    name: 'CourseLearn',
    component: () => import('@/views/CourseLearnView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/my-courses',
    name: 'MyCourses',
    component: () => import('@/views/MyCoursesView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/forum/notifications',
    name: 'ForumNotifications',
    component: () => import('@/views/ForumNotificationsView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/forum/user/:id',
    name: 'ForumUserProfile',
    component: () => import('@/views/ForumUserProfileView.vue'),
  },
  {
    path: '/forum/profile',
    redirect: (to) => {
      const userStore = useUserStore()
      const userId = userStore.user?.id
      return userId ? `/forum/user/${userId}` : '/login'
    },
  },
  {
    path: '/notifications',
    name: 'Notifications',
    component: () => import('@/views/NotificationsView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/browse-history',
    name: 'BrowseHistory',
    component: () => import('@/views/BrowseHistoryView.vue'),
    meta: { requiresAuth: true },
  },
  // 匠人端
  {
    path: '/artisan/dashboard',
    name: 'ArtisanDashboard',
    component: () => import('@/views/artisan/DashboardView.vue'),
    meta: { requiresAuth: true, requiresArtisan: true },
  },
  {
    path: '/artisan/products',
    name: 'ArtisanProducts',
    component: () => import('@/views/artisan/ProductsView.vue'),
    meta: { requiresAuth: true, requiresArtisan: true },
  },
  {
    path: '/artisan/orders',
    name: 'ArtisanOrders',
    component: () => import('@/views/artisan/OrdersView.vue'),
    meta: { requiresAuth: true, requiresArtisan: true },
  },
  {
    path: '/artisan/custom',
    name: 'ArtisanCustom',
    component: () => import('@/views/artisan/CustomView.vue'),
    meta: { requiresAuth: true, requiresArtisan: true },
  },
  {
    path: '/artisan/courses',
    name: 'ArtisanCourses',
    component: () => import('@/views/artisan/CoursesView.vue'),
    meta: { requiresAuth: true, requiresArtisan: true },
  },
  {
    path: '/artisan/courses/new',
    name: 'ArtisanCourseNew',
    component: () => import('@/views/artisan/CourseEditView.vue'),
    meta: { requiresAuth: true, requiresArtisan: true },
  },
  {
    path: '/artisan/courses/:id/edit',
    name: 'ArtisanCourseEdit',
    component: () => import('@/views/artisan/CourseEditView.vue'),
    meta: { requiresAuth: true, requiresArtisan: true },
  },
  {
    path: '/artisan/forum',
    name: 'ArtisanForum',
    component: () => import('@/views/artisan/ForumView.vue'),
    meta: { requiresAuth: true, requiresArtisan: true },
  },
  {
    path: '/artisan/settings',
    name: 'ArtisanSettings',
    component: () => import('@/views/artisan/SettingsView.vue'),
    meta: { requiresAuth: true, requiresArtisan: true },
  },
  // 管理员端
  {
    path: '/admin',
    component: () => import('@/views/admin/AdminLayout.vue'),
    meta: { requiresAuth: true, requiresAdmin: true },
    children: [
      {
        path: '',
        name: 'AdminDashboard',
        component: () => import('@/views/admin/DashboardView.vue'),
      },
      {
        path: 'users',
        name: 'AdminUsers',
        component: () => import('@/views/admin/UsersView.vue'),
      },
      {
        path: 'artisans',
        name: 'AdminArtisans',
        component: () => import('@/views/admin/ArtisansView.vue'),
      },
      {
        path: 'products',
        name: 'AdminProducts',
        component: () => import('@/views/admin/ProductsView.vue'),
      },
      {
        path: 'orders',
        name: 'AdminOrders',
        component: () => import('@/views/admin/OrdersView.vue'),
      },
      {
        path: 'categories',
        name: 'AdminCategories',
        component: () => import('@/views/admin/CategoriesView.vue'),
      },
      {
        path: 'courses',
        name: 'AdminCourses',
        component: () => import('@/views/admin/CoursesView.vue'),
      },
      {
        path: 'forum',
        name: 'AdminForum',
        component: () => import('@/views/admin/ForumView.vue'),
      },
      {
        path: 'banners',
        name: 'AdminBanners',
        component: () => import('@/views/admin/BannersView.vue'),
      },
      {
        path: 'commissions',
        name: 'AdminCommissions',
        component: () => import('@/views/admin/CommissionsView.vue'),
      },
      {
        path: 'merchant/applications',
        name: 'AdminMerchantApplications',
        component: () => import('@/views/admin/MerchantApplicationsView.vue'),
      },
      {
        path: 'merchant/list',
        name: 'AdminMerchantList',
        component: () => import('@/views/admin/MerchantListView.vue'),
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  const userStore = useUserStore()
  // Use Pinia store as single source of truth — localStorage may contain stale tokens
  const token = userStore.token
  const user = userStore.user

  // Clear browse_as_user flag when navigating to artisan routes
  if (to.meta.requiresArtisan) {
    sessionStorage.removeItem('browse_as_user')
  }

  // Only redirect to login if neither token nor user exists (stale token alone won't block)
  if (to.meta.requiresAuth && (!token || !user)) {
    next({ name: 'Login', query: { redirect: to.fullPath } })
    return
  }

  if (to.meta.requiresArtisan && user?.role !== 'artisan') {
    next({ name: 'Home' })
    return
  }

  if (to.meta.requiresAdmin && user?.role !== 'admin') {
    next({ name: 'Home' })
    return
  }

  // Only redirect authenticated users away from guest routes if they have BOTH token and user
  if (to.meta.guest && token && user) {
    next({ name: 'Home' })
    return
  }

  next()
})

export default router
