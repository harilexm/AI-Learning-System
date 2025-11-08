import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import LoginView from '../views/LoginView.vue'
import RegisterView from '../views/RegisterView.vue'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    // PUBLIC ROUTES
    {
      path: '/',
      name: 'home',
      component: HomeView
    },
    {
      path: '/about',
      name: 'about',
      component: () => import('../views/AboutView.vue')
    },
    {
      path: '/login',
      name: 'login',
      component: LoginView
    },
    {
      path: '/register',
      name: 'register',
      component: RegisterView
    },

    // PROTECTED ROUTES (BY ROLE)
    // Student Dashboard
    {
      path: '/dashboard',
      name: 'dashboard',
      component: () => import('../views/DashboardView.vue'),
      meta: { 
        requiresAuth: true,
        allowedRoles: ['student', 'teacher', 'administrator'] // Anyone logged in can see a basic dashboard
      }
    },
    // Teacher Dashboard
    {
      path: '/teacher-dashboard',
      name: 'teacher-dashboard',
      component: () => import('../views/TeacherDashboardView.vue'),
      meta: { 
        requiresAuth: true,
        allowedRoles: ['teacher', 'administrator'] // Only Teachers and Admins
      }
    },
    // Admin Dashboard
    {
      path: '/admin',
      name: 'admin',
      component: () => import('../views/AdminDashboardView.vue'),
      meta: { 
        requiresAuth: true,
        allowedRoles: ['administrator'] // Strictly Admins only
      }
    },
    {
      path: '/profile',
      name: 'profile',
      component: () => import('../views/ProfileView.vue'),
      meta: {
        requiresAuth: true
        // No 'allowedRoles' means any authenticated user can access it
      }
    },
    
    // ... (inside the routes array)
    {
      path: '/manage-courses',
      name: 'manage-courses',
      component: () => import('../views/CourseManagementView.vue'),
      meta: { 
        requiresAuth: true,
        allowedRoles: ['teacher', 'administrator'] // Protect this route
      }
    },
    
        // ... (inside the routes array)
    {
      path: '/courses/:courseId', // e.g., /courses/some-uuid-string
      name: 'course-details',
      component: () => import('../views/CourseDetailView.vue'),
      meta: { 
        requiresAuth: true,
        // Accessible by anyone logged in, as they might want to browse
        allowedRoles: ['student', 'teacher', 'administrator']
      }
    },
        // ... (inside the routes array, probably after 'manage-courses')
    {
      path: '/courses/:courseId/progress',
      name: 'course-progress',
      component: () => import('../views/CourseProgressView.vue'),
      meta: { 
        requiresAuth: true,
        allowedRoles: ['teacher', 'administrator']
      }
    },
    // --- THIS IS THE MISSING PIECE ---
    // Add this route object to your `routes` array.
    // A good place is after the 'course-details' route.
    {
      path: '/quiz/:contentId/take',
      name: 'quiz-player',
      component: () => import('../views/QuizPlayerView.vue'),
      meta: { 
        requiresAuth: true,
        allowedRoles: ['student'] // Only students should be taking quizzes
      }
    },
    {
      path: '/forgot-password',
      name: 'forgot-password',
      component: () => import('../views/ForgotPasswordView.vue')
    },
    {
      path: '/reset-password',
      name: 'reset-password',
      component: () => import('../views/ResetPasswordView.vue')
    },
  ]
})

// ADVANCED NAVIGATION GUARD
// This function handles both authentication and authorization.
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore();
  const isAuthenticated = authStore.isAuthenticated;
  
  // Try to fetch profile if a token exists but user info is missing (e.g., on page refresh)
  if (isAuthenticated && !authStore.user) {
    await authStore.fetchProfile();
  }

  const userRoles = authStore.userRoles;
  const requiresAuth = to.meta.requiresAuth;
  const allowedRoles = to.meta.allowedRoles;

  // If route requires authentication and user is not logged in
  if (requiresAuth && !isAuthenticated) {
    return next({ name: 'login' }); // Redirect to login page
  }
  
  // If route requires a specific role and user does not have it
  if (allowedRoles && allowedRoles.length > 0) {
    const isAuthorized = userRoles.some(role => allowedRoles.includes(role));
    if (!isAuthorized) {
      // Redirect unauthorized user to their default dashboard
      if (authStore.isAdmin) return next({ name: 'admin' });
      if (authStore.isTeacher) return next({ name: 'teacher-dashboard' });
      return next({ name: 'dashboard' });
    }
  }

  // If a logged-in user tries to access login/register pages
  if (isAuthenticated && (to.name === 'login' || to.name === 'register')) {
    // Redirect them away from login/register to their dashboard
    if (authStore.isAdmin) return next({ name: 'admin' });
    if (authStore.isTeacher) return next({ name: 'teacher-dashboard' });
    return next({ name: 'dashboard' });
  }

  // Otherwise, allow navigation
  next();
});

export default router