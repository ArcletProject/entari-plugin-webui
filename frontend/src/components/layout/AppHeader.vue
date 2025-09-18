<script setup lang="ts">
import { isCollapse } from './isCollapse';
import { useAuthStore } from '@/stores/auth';
import { logout, updateUser } from '@/api/users';
import { useRouter } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import 'element-plus/theme-chalk/el-message.css';
import 'element-plus/theme-chalk/el-message-box.css';
import '@/styles/theme.scss'
import { ref } from 'vue';
import { Sunny, Moon } from '@element-plus/icons-vue'

const authStore = useAuthStore();
const router = useRouter();
const dialogVisible = ref(false);
const activeTab = ref('info');
const isDark = inject<Ref<boolean>>('isDark')!
// const toggleDark = inject<() => boolean>('toggleDark')!

// 用户信息表单
const userForm = ref({
    username: authStore.user?.name ?? '未知用户',
    email: authStore.user?.email ?? 'user@example.com',
    role: '管理员',
    status: '正常'
});

// 密码表单
const passwordForm = ref({
    currentPassword: '',
    newPassword: '',
    confirmPassword: ''
});

// 处理退出登录
const handleLogout = async () => {
    await ElMessageBox.confirm('确定要退出吗？', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
    }).catch(() => {
        ElMessage.info('已取消退出');
        return new Promise(() => { });
    });

    await logout().catch(() => { });
    authStore.logout();
    ElMessage.success('退出成功');
    router.push('/login');
};

// 打开用户设置对话框
const openUserSettings = () => {
    dialogVisible.value = true;
};

const changePassword = async () => {
    if (passwordForm.value.newPassword !== passwordForm.value.confirmPassword) {
        ElMessage.error('两次密码不一致')
        return
    }
    const res = await updateUser({ password: passwordForm.value.newPassword })
    if (res.success) {
        ElMessage.success('密码已更新')
        dialogVisible.value = false
        passwordForm.value = { currentPassword: '', newPassword: '', confirmPassword: '' }
    } else {
        ElMessage.error(res.message || '修改失败')
    }
}

const saveUserInfo = async () => {
    const res = await updateUser({ email: userForm.value.email })
    if (res.success) {
        ElMessage.success('邮箱已更新')
        authStore.user!.email = userForm.value.email
        dialogVisible.value = false
    } else {
        ElMessage.error(res.message || '修改失败')
    }
}
</script>

<template>
    <el-header>
        <el-icon @click="isCollapse = !isCollapse" class="fold-icon">
            <IEpExpand v-show="isCollapse" />
            <IEpFold v-show="!isCollapse" />
        </el-icon>

        <div class="header-actions">
            <el-switch v-model="isDark" class="dark-switch" inline-prompt :active-icon="Moon" :inactive-icon="Sunny"
                style="--el-switch-on-color: #409eff; --el-switch-off-color: #bbb" />

            <el-dropdown>
                <span class="el-dropdown-link">
                    <el-avatar :size="32"
                        :src="'https://cube.elemecdn.com/3/7c/3ea6beec64369c2642b92c6726f1epng.png'" />
                    <el-icon class="el-icon--right">
                        <i-ep-arrow-down />
                    </el-icon>
                </span>

                <template #dropdown>
                    <el-dropdown-menu>
                        <el-dropdown-item @click="openUserSettings">设置用户信息</el-dropdown-item>
                        <el-dropdown-item divided @click="handleLogout">退出</el-dropdown-item>
                    </el-dropdown-menu>
                </template>
            </el-dropdown>
        </div>

        <!-- 用户设置对话框 -->
        <el-dialog v-model="dialogVisible" title="用户设置" width="500px">
            <el-tabs v-model="activeTab" type="border-card">
                <!-- 用户信息标签页 -->
                <el-tab-pane label="用户信息" name="info">
                    <el-form :model="userForm" label-width="100px" style="margin-top: 20px;">
                        <el-form-item label="用户名">
                            <el-input v-model="userForm.username" disabled />
                        </el-form-item>
                        <el-form-item label="邮箱">
                            <el-input v-model="userForm.email" />
                        </el-form-item>
                        <el-form-item label="角色">
                            <el-select v-model="userForm.role" disabled>
                                <el-option label="管理员" value="管理员" />
                                <el-option label="普通用户" value="普通用户" />
                            </el-select>
                        </el-form-item>
                        <el-form-item label="状态">
                            <el-select v-model="userForm.status" disabled>
                                <el-option label="正常" value="正常" />
                                <el-option label="禁用" value="禁用" />
                            </el-select>
                        </el-form-item>
                    </el-form>
                </el-tab-pane>

                <!-- 修改密码标签页 -->
                <el-tab-pane label="修改密码" name="password">
                    <el-form :model="passwordForm" label-width="100px" style="margin-top: 20px;">
                        <el-form-item label="当前密码">
                            <el-input v-model="passwordForm.currentPassword" type="password" show-password />
                        </el-form-item>
                        <el-form-item label="新密码">
                            <el-input v-model="passwordForm.newPassword" type="password" show-password />
                        </el-form-item>
                        <el-form-item label="确认密码">
                            <el-input v-model="passwordForm.confirmPassword" type="password" show-password />
                        </el-form-item>
                    </el-form>
                </el-tab-pane>
            </el-tabs>

            <template #footer>
                <div class="dialog-footer">
                    <el-button @click="dialogVisible = false">取消</el-button>
                    <el-button v-if="activeTab === 'info'" type="primary" @click="saveUserInfo">
                        保存信息
                    </el-button>
                    <el-button v-else type="primary" @click="changePassword">
                        修改密码
                    </el-button>
                </div>
            </template>
        </el-dialog>
    </el-header>
</template>

<style lang="scss" scoped>
.el-header {
    display: flex;
    align-items: center;
    background-color: var(--el-bg);
    border-bottom: 1px solid var(--el-border);
    box-shadow: 0 1px 4px var(--el-shadow);
    color: var(--el-text);
    transition: background-color 0.3s, color 0.3s;

    .el-icon {
        margin-right: 20px;
        font-size: 20px;
        cursor: pointer;
        transition: color 0.3s;
        color: var(--el-icon);

        &:hover {
            color: var(--el-icon-hover);
        }
    }
}

.el-dropdown {
    margin-left: auto;

    .el-dropdown-link {
        display: flex;
        justify-content: center;
        align-items: center;
        cursor: pointer;
        transition: all 0.3s;

        &:hover {
            .el-avatar {
                box-shadow: 0 0 0 2px var(--el-avatar-ring);
            }
        }

        .el-avatar {
            transition: all 0.3s;
        }

        .el-icon {
            margin-right: 0;
            margin-left: 5px;
            font-size: 14px;
            color: var(--el-icon);
        }
    }
}

.dialog-footer {
    display: flex;
    justify-content: flex-end;
    padding: 10px 0;
}

.el-tabs {
    box-shadow: none;
    border: none;

    :deep(.el-tabs__content) {
        padding: 0 20px;
    }
}

.fold-icon {
    margin-right: 20px;
    font-size: 20px;
    cursor: pointer;
    color: var(--el-icon);
    transition: color 0.3s;

    &:hover {
        color: var(--el-icon-hover);
    }
}

.header-actions {
    display: flex;
    align-items: center;
    margin-left: auto;
    gap: 8px;
}


.dark-icon {
    margin-left: auto;
    margin-right: 16px;
    cursor: pointer;
    color: var(--el-icon);
    transition: color 0.3s;

    &:hover {
        color: var(--el-icon-hover);
    }
}

.dark-switch {
    margin-left: auto;
    margin-right: 12px;
}
</style>