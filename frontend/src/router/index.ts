import { createRouter, createWebHashHistory } from 'vue-router';
import AppLayout from '@/components/layout/AppLayout.vue';
import IndexView from '@/views/IndexView.vue';
import LoginView from '@/views/login/LoginView.vue';
import ErrorPage from '@/views/ErrorPage.vue';
import { useAuthStore } from '@/stores/auth';

const router = createRouter({
  history: createWebHashHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: LoginView,
    },
    {
      path: '/',
      name: 'home',
      component: AppLayout,
      meta: { requiresAuth: true },
      children: [
        {
          path: '',
          component: IndexView,
        },
        {
          path: '/menus',
          name: 'menus',
          component: () => import('@/views/menu/ExamplesIndex.vue'),
        },
        {
          path: '/control',
          name: 'control',
          component: () => import('@/views/control/ControlView.vue'),
        },
        {
          path: '/instances',
          name: 'instances',
          component: () => import('@/views/instance/InstanceManager.vue'),
        },
        {
          path: '/plugin',
          name: 'plugin',
          component: () => import('@/views/plugin/PluginView.vue'),
        },
        {
          path: '/plugin-market',
          name: 'plugin-market',
          component: () => import('@/views/plugin/PluginMarketView.vue'),
        },
        {
          path: '/set',
          name: 'set',
          component: () => import('@/views/set/SetView.vue'),
        },
        {
          path: '/support/docs',
          name: 'docs',
          component: () => import('@/views/support/DocsView.vue'),
        },
        {
          path: '/support/community',
          name: 'community',
          component: () => import('@/views/support/CommunityView.vue'),
        },
        {
          path: '/plugin/plugin-manager',
          name: 'plugin-manager',
          component: () => import('@/views/plugin/PluginManager.vue'),
        },
        {
          path: '/about/contributors',
          name: 'contributors',
          component: () => import('@/views/about/ContributorsView.vue'),
        },
        {
          path: '/about/project-info',
          name: 'project-info',
          component: () => import('@/views/about/ProjectInfoView.vue'),
        },
        {
          path: '/:xxx(.*)*',
          name: 'ErrorPage',
          component: ErrorPage,
        },
      ]
    },
  ],
});

router.beforeEach((to, from, next) => {
  if (to.matched.some(r=>r.meta?.requiresAuth)){
    const store = useAuthStore();
    if (!store.token) {
      // 如果没有token，重定向到登录页面
      next({ name: 'login' ,query: { redirect: to.fullPath } });
      return;
    }
  }
  next()
});

export default router;
