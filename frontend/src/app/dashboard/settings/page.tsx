'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/store/authStore';
import { useThemeStore } from '@/store/themeStore';
import { ArrowLeft, User, Lock, Bell, Shield, Trash, Eye, EyeOff, CheckCircle2, XCircle, AlertCircle, Calendar, Mail, Monitor, Smartphone, Tablet, Clock, MapPin } from 'lucide-react';
import { apiClient } from '@/lib/api';

export default function SettingsPage() {
    const router = useRouter();
    const { user, logout, fetchUser } = useAuthStore();
    const { isDarkMode } = useThemeStore();
    const [activeTab, setActiveTab] = useState('profile');

    // Profile state
    const [fullName, setFullName] = useState(user?.full_name || '');
    const [profileLoading, setProfileLoading] = useState(false);
    const [profileMessage, setProfileMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null);

    // Password state
    const [currentPassword, setCurrentPassword] = useState('');
    const [newPassword, setNewPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [showCurrentPassword, setShowCurrentPassword] = useState(false);
    const [showNewPassword, setShowNewPassword] = useState(false);
    const [showConfirmPassword, setShowConfirmPassword] = useState(false);
    const [passwordLoading, setPasswordLoading] = useState(false);
    const [passwordMessage, setPasswordMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null);

    // Delete account state
    const [deleteLoading, setDeleteLoading] = useState(false);
    const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

    const tabs = [
        { id: 'profile', name: 'Profile', icon: User },
        { id: 'password', name: 'Password', icon: Lock },
        { id: 'preferences', name: 'Preferences', icon: Bell },
        { id: 'security', name: 'Security', icon: Shield },
        { id: 'account', name: 'Account', icon: Trash },
    ];

    // Password strength calculator
    const calculatePasswordStrength = (password: string): { strength: number, label: string, color: string } => {
        if (!password) return { strength: 0, label: '', color: '' };

        let strength = 0;
        if (password.length >= 8) strength += 25;
        if (password.length >= 12) strength += 25;
        if (/[a-z]/.test(password) && /[A-Z]/.test(password)) strength += 20;
        if (/\d/.test(password)) strength += 15;
        if (/[^a-zA-Z\d]/.test(password)) strength += 15;

        if (strength < 40) return { strength, label: 'Weak', color: 'text-red-500' };
        if (strength < 70) return { strength, label: 'Medium', color: 'text-yellow-500' };
        return { strength, label: 'Strong', color: 'text-emerald-500' };
    };

    const passwordStrength = calculatePasswordStrength(newPassword);

    const handleUpdateProfile = async (e: React.FormEvent) => {
        e.preventDefault();
        setProfileLoading(true);
        setProfileMessage(null);

        try {
            await apiClient.patch('/auth/update-profile', {
                full_name: fullName
            });

            // Refresh user data
            await fetchUser();

            setProfileMessage({ type: 'success', text: 'Profile updated successfully!' });
            setTimeout(() => setProfileMessage(null), 3000);
        } catch (error: any) {
            const errorMsg = error.response?.data?.detail || 'Failed to update profile';
            setProfileMessage({ type: 'error', text: errorMsg });
            setTimeout(() => setProfileMessage(null), 5000);
        } finally {
            setProfileLoading(false);
        }
    };

    const handleUpdatePassword = async (e: React.FormEvent) => {
        e.preventDefault();
        setPasswordLoading(true);
        setPasswordMessage(null);

        // Validation
        if (!currentPassword || !newPassword || !confirmPassword) {
            setPasswordMessage({ type: 'error', text: 'All fields are required' });
            setPasswordLoading(false);
            setTimeout(() => setPasswordMessage(null), 5000);
            return;
        }

        if (newPassword !== confirmPassword) {
            setPasswordMessage({ type: 'error', text: 'New passwords do not match' });
            setPasswordLoading(false);
            setTimeout(() => setPasswordMessage(null), 5000);
            return;
        }

        if (newPassword.length < 6) {
            setPasswordMessage({ type: 'error', text: 'Password must be at least 6 characters' });
            setPasswordLoading(false);
            setTimeout(() => setPasswordMessage(null), 5000);
            return;
        }

        try {
            await apiClient.patch('/auth/change-password', {
                current_password: currentPassword,
                new_password: newPassword
            });

            setPasswordMessage({ type: 'success', text: 'Password updated successfully!' });
            setCurrentPassword('');
            setNewPassword('');
            setConfirmPassword('');
            setTimeout(() => setPasswordMessage(null), 3000);
        } catch (error: any) {
            const errorMsg = error.response?.data?.detail || 'Failed to update password';
            setPasswordMessage({ type: 'error', text: errorMsg });
            setTimeout(() => setPasswordMessage(null), 5000);
        } finally {
            setPasswordLoading(false);
        }
    };

    const handleDeleteAccount = async () => {
        setDeleteLoading(true);

        try {
            await apiClient.delete('/auth/delete-account');

            // Logout and redirect
            logout();
            router.push('/');
        } catch (error: any) {
            const errorMsg = error.response?.data?.detail || 'Failed to delete account';
            alert(errorMsg);
        } finally {
            setDeleteLoading(false);
            setShowDeleteConfirm(false);
        }
    };

    return (
        <div className={`min-h-screen ${isDarkMode ? 'bg-[#0a0f1e]' : 'bg-gray-50'} p-6`}>
            <div className="max-w-4xl mx-auto">
                {/* Header */}
                <div className="mb-6">
                    <button
                        onClick={() => router.push('/dashboard')}
                        className={`flex items-center gap-2 mb-4 ${isDarkMode ? 'text-gray-400 hover:text-white' : 'text-gray-600 hover:text-gray-900'} transition-colors`}
                    >
                        <ArrowLeft className="w-5 h-5" />
                        Back to Dashboard
                    </button>
                    <h1 className={`text-3xl font-bold ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
                        Settings
                    </h1>
                </div>

                {/* Settings Content */}
                <div className={`rounded-2xl ${isDarkMode ? 'bg-gray-900/50 border border-gray-800' : 'bg-white border border-gray-200'} overflow-hidden`}>
                    {/* Tabs */}
                    <div className={`flex border-b ${isDarkMode ? 'border-gray-800' : 'border-gray-200'} overflow-x-auto`}>
                        {tabs.map((tab) => {
                            const Icon = tab.icon;
                            return (
                                <button
                                    key={tab.id}
                                    onClick={() => setActiveTab(tab.id)}
                                    className={`flex items-center gap-2 px-6 py-4 text-sm font-medium whitespace-nowrap transition-colors ${activeTab === tab.id
                                        ? `${isDarkMode ? 'text-emerald-400 border-b-2 border-emerald-400 bg-emerald-500/5' : 'text-emerald-600 border-b-2 border-emerald-600 bg-emerald-50'}`
                                        : `${isDarkMode ? 'text-gray-500 hover:text-gray-300' : 'text-gray-600 hover:text-gray-900'}`
                                        }`}
                                >
                                    <Icon className="w-4 h-4" />
                                    {tab.name}
                                </button>
                            );
                        })}
                    </div>

                    {/* Tab Content */}
                    <div className="p-8">
                        {activeTab === 'profile' && (
                            <form onSubmit={handleUpdateProfile} className="space-y-6">
                                <h2 className={`text-2xl font-bold ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
                                    Profile Information
                                </h2>

                                {profileMessage && (
                                    <div className={`p-4 rounded-lg ${profileMessage.type === 'success'
                                        ? 'bg-emerald-500/10 border border-emerald-500/30 text-emerald-400'
                                        : 'bg-red-500/10 border border-red-500/30 text-red-400'}`}>
                                        {profileMessage.text}
                                    </div>
                                )}

                                <div className="space-y-4">
                                    <div>
                                        <label className={`block text-sm font-medium mb-2 ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                                            Email
                                        </label>
                                        <input
                                            type="email"
                                            value={user?.email || ''}
                                            disabled
                                            className={`w-full px-4 py-3 rounded-lg ${isDarkMode ? 'bg-gray-800 border-gray-700 text-gray-400' : 'bg-gray-100 border-gray-300 text-gray-500'} border cursor-not-allowed`}
                                        />
                                        <p className={`text-xs mt-1 ${isDarkMode ? 'text-gray-500' : 'text-gray-400'}`}>Email cannot be changed</p>
                                    </div>
                                    <div>
                                        <label className={`block text-sm font-medium mb-2 ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                                            Full Name
                                        </label>
                                        <input
                                            type="text"
                                            value={fullName}
                                            onChange={(e) => setFullName(e.target.value)}
                                            className={`w-full px-4 py-3 rounded-lg ${isDarkMode ? 'bg-gray-800 border-gray-700 text-white' : 'bg-white border-gray-300 text-gray-900'} border focus:ring-2 focus:ring-emerald-500 focus:border-transparent outline-none`}
                                            required
                                        />
                                    </div>
                                    <button
                                        type="submit"
                                        disabled={profileLoading}
                                        className="bg-gradient-to-r from-emerald-500 to-cyan-500 text-white px-6 py-3 rounded-lg font-semibold hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed"
                                    >
                                        {profileLoading ? 'Saving...' : 'Save Changes'}
                                    </button>
                                </div>
                            </form>
                        )}

                        {activeTab === 'password' && (
                            <form onSubmit={handleUpdatePassword} className="space-y-6">
                                <h2 className={`text-2xl font-bold ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
                                    Change Password
                                </h2>

                                {passwordMessage && (
                                    <div className={`p-4 rounded-lg ${passwordMessage.type === 'success'
                                        ? 'bg-emerald-500/10 border border-emerald-500/30 text-emerald-400'
                                        : 'bg-red-500/10 border border-red-500/30 text-red-400'}`}>
                                        {passwordMessage.text}
                                    </div>
                                )}

                                <div className="space-y-4">
                                    <div>
                                        <label className={`block text-sm font-medium mb-2 ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                                            Current Password
                                        </label>
                                        <div className="relative">
                                            <input
                                                type={showCurrentPassword ? "text" : "password"}
                                                value={currentPassword}
                                                onChange={(e) => setCurrentPassword(e.target.value)}
                                                className={`w-full px-4 py-3 pr-12 rounded-lg ${isDarkMode ? 'bg-gray-800 border-gray-700 text-white' : 'bg-white border-gray-300 text-gray-900'} border focus:ring-2 focus:ring-emerald-500 focus:border-transparent outline-none transition-all`}
                                                required
                                                placeholder="Enter current password"
                                            />
                                            <button
                                                type="button"
                                                onClick={() => setShowCurrentPassword(!showCurrentPassword)}
                                                className={`absolute right-3 top-1/2 -translate-y-1/2 ${isDarkMode ? 'text-gray-400 hover:text-gray-300' : 'text-gray-500 hover:text-gray-700'} transition-colors`}
                                            >
                                                {showCurrentPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                                            </button>
                                        </div>
                                    </div>
                                    <div>
                                        <label className={`block text-sm font-medium mb-2 ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                                            New Password
                                        </label>
                                        <div className="relative">
                                            <input
                                                type={showNewPassword ? "text" : "password"}
                                                value={newPassword}
                                                onChange={(e) => setNewPassword(e.target.value)}
                                                className={`w-full px-4 py-3 pr-12 rounded-lg ${isDarkMode ? 'bg-gray-800 border-gray-700 text-white' : 'bg-white border-gray-300 text-gray-900'} border focus:ring-2 focus:ring-emerald-500 focus:border-transparent outline-none transition-all`}
                                                required
                                                placeholder="Enter new password"
                                            />
                                            <button
                                                type="button"
                                                onClick={() => setShowNewPassword(!showNewPassword)}
                                                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-300"
                                            >
                                                {showNewPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                                            </button>
                                        </div>
                                    </div>
                                    <div>
                                        <label className={`block text-sm font-medium mb-2 ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                                            Confirm New Password
                                        </label>
                                        <div className="relative">
                                            <input
                                                type={showConfirmPassword ? "text" : "password"}
                                                value={confirmPassword}
                                                onChange={(e) => setConfirmPassword(e.target.value)}
                                                className={`w-full px-4 py-3 pr-12 rounded-lg ${isDarkMode ? 'bg-gray-800 border-gray-700 text-white' : 'bg-white border-gray-300 text-gray-900'} border focus:ring-2 focus:ring-emerald-500 focus:border-transparent outline-none transition-all`}
                                                required
                                                placeholder="Confirm new password"
                                            />
                                            <button
                                                type="button"
                                                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                                                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-300"
                                            >
                                                {showConfirmPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                                            </button>
                                        </div>
                                    </div>
                                    <button
                                        type="submit"
                                        disabled={passwordLoading}
                                        className="bg-gradient-to-r from-emerald-500 to-cyan-500 text-white px-6 py-3 rounded-lg font-semibold hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed"
                                    >
                                        {passwordLoading ? 'Updating...' : 'Update Password'}
                                    </button>
                                </div>
                            </form>
                        )}

                        {activeTab === 'preferences' && (
                            <div className="space-y-6">
                                <h2 className={`text-2xl font-bold ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
                                    Preferences
                                </h2>
                                <p className={`${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                                    Notification and display preferences coming soon...
                                </p>
                            </div>
                        )}

                        {activeTab === 'security' && (
                            <SecurityTab
                                isDarkMode={isDarkMode}
                            />
                        )}

                        {activeTab === 'account' && (
                            <div className="space-y-6">
                                <h2 className={`text-2xl font-bold ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
                                    Delete Account
                                </h2>
                                <div className={`p-4 rounded-lg ${isDarkMode ? 'bg-red-500/10 border border-red-500/30' : 'bg-red-50 border border-red-200'}`}>
                                    <p className={`text-sm ${isDarkMode ? 'text-red-400' : 'text-red-600'}`}>
                                        ⚠️ This action is permanent and cannot be undone. All your data, analyses, and watchlists will be permanently deleted.
                                    </p>
                                </div>

                                {!showDeleteConfirm ? (
                                    <button
                                        onClick={() => setShowDeleteConfirm(true)}
                                        className="bg-red-500 text-white px-6 py-3 rounded-lg font-semibold hover:bg-red-600 transition-colors"
                                    >
                                        Delete My Account
                                    </button>
                                ) : (
                                    <div className="space-y-4">
                                        <p className={`font-semibold ${isDarkMode ? 'text-red-400' : 'text-red-600'}`}>
                                            Are you absolutely sure? This cannot be undone.
                                        </p>
                                        <div className="flex gap-4">
                                            <button
                                                onClick={handleDeleteAccount}
                                                disabled={deleteLoading}
                                                className="bg-red-500 text-white px-6 py-3 rounded-lg font-semibold hover:bg-red-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                                            >
                                                {deleteLoading ? 'Deleting...' : 'Yes, Delete Forever'}
                                            </button>
                                            <button
                                                onClick={() => setShowDeleteConfirm(false)}
                                                disabled={deleteLoading}
                                                className={`px-6 py-3 rounded-lg font-semibold transition-colors ${isDarkMode ? 'bg-gray-800 text-white hover:bg-gray-700' : 'bg-gray-200 text-gray-900 hover:bg-gray-300'}`}
                                            >
                                                Cancel
                                            </button>
                                        </div>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}

// Security Tab Component
function SecurityTab({ isDarkMode }: { isDarkMode: boolean }) {
    const [loginHistory, setLoginHistory] = useState<any[]>([]);
    const [activeSessions, setActiveSessions] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [revoking, setRevoking] = useState<number | null>(null);

    useEffect(() => {
        fetchSecurityData();
    }, []);

    const fetchSecurityData = async () => {
        setLoading(true);
        try {
            // Get tracking headers
            const { TrackingHeaders } = await import('@/lib/tracking-headers');
            const trackingHeaders = await TrackingHeaders.getHeaders();

            const [historyRes, sessionsRes] = await Promise.all([
                apiClient.get('/api/security/login-history?limit=20', {
                    headers: trackingHeaders as any
                }),
                apiClient.get('/api/security/active-sessions', {
                    headers: trackingHeaders as any
                })
            ]);
            setLoginHistory(historyRes.data);
            setActiveSessions(sessionsRes.data);
        } catch (error: any) {
            console.error('Failed to fetch security data:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleRevokeSession = async (tokenId: number) => {
        console.log('[REVOKE] Starting revoke for token ID:', tokenId);
        if (!confirm('Revoke this session? You will be logged out on that device.')) {
            console.log('[REVOKE] User cancelled');
            return;
        }

        console.log('[REVOKE] User confirmed, setting revoking state');
        setRevoking(tokenId);
        try {
            // Get tracking headers
            console.log('[REVOKE] Getting tracking headers...');
            const { TrackingHeaders } = await import('@/lib/tracking-headers');
            const trackingHeaders = await TrackingHeaders.getHeaders();
            console.log('[REVOKE] Got headers:', trackingHeaders);

            console.log('[REVOKE] Making POST request...');
            const response = await apiClient.post(`/api/security/revoke-session/${tokenId}`, {}, {
                headers: trackingHeaders as any
            });
            console.log('[REVOKE] Success:', response);

            console.log('[REVOKE] Refreshing security data...');
            await fetchSecurityData(); // Refresh
            console.log('[REVOKE] Done!');
        } catch (error: any) {
            console.error('[REVOKE] Error:', error);
            console.error('[REVOKE] Error response:', error.response);
            alert(error.response?.data?.detail || 'Failed to revoke session');
        } finally {
            console.log('[REVOKE] Clearing revoking state');
            setRevoking(null);
        }
    };

    const handleLogoutAllDevices = async () => {
        if (!confirm('Logout from all other devices? Only this session will remain active.')) return;

        try {
            // Get tracking headers
            const { TrackingHeaders } = await import('@/lib/tracking-headers');
            const trackingHeaders = await TrackingHeaders.getHeaders();

            const response = await apiClient.post('/api/security/revoke-all-sessions', {}, {
                headers: trackingHeaders as any
            });
            alert(response.data.message || 'Logged out from all other devices');
            await fetchSecurityData(); // Refresh
        } catch (error: any) {
            alert(error.response?.data?.detail || 'Failed to logout from devices');
        }
    };

    const getDeviceIcon = (deviceType: string) => {
        switch (deviceType?.toLowerCase()) {
            case 'mobile':
                return <Smartphone className="w-5 h-5" />;
            case 'tablet':
                return <Tablet className="w-5 h-5" />;
            case 'desktop':
            default:
                return <Monitor className="w-5 h-5" />;
        }
    };

    const formatRelativeTime = (dateString: string) => {
        const date = new Date(dateString);
        const now = new Date();
        const diffMs = now.getTime() - date.getTime();
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);

        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins}m ago`;
        if (diffHours < 24) return `${diffHours}h ago`;
        if (diffDays < 7) return `${diffDays}d ago`;
        // Use ISO date to avoid hydration mismatch
        return date.toISOString().split('T')[0];
    };

    const formatDateTime = (dateString: string) => {
        const date = new Date(dateString);
        const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
        const year = date.getFullYear();
        const month = months[date.getMonth()];
        const day = date.getDate();
        const hours = date.getHours().toString().padStart(2, '0');
        const mins = date.getMinutes().toString().padStart(2, '0');
        return `${month} ${day}, ${year}, ${hours}:${mins}`;
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center py-12">
                <div className={`text-${isDarkMode ? 'gray-400' : 'gray-600'}`}>Loading security data...</div>
            </div>
        );
    }

    return (
        <div className="space-y-8">
            {/* Active Sessions */}
            <div className="space-y-4">
                <div>
                    <h2 className={`text-2xl font-bold ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
                        Active Sessions
                    </h2>
                    <p className={`text-sm mt-1 ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                        You can have maximum 2 active sessions. Oldest sessions are automatically logged out.
                    </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {activeSessions.map(session => (
                        <div
                            key={session.id}
                            className={`p-6 rounded-xl border-2 transition-all ${session.is_current
                                ? `${isDarkMode ? 'border-emerald-500 bg-emerald-500/5' : 'border-emerald-600 bg-emerald-50'}`
                                : `${isDarkMode ? 'border-gray-700 bg-gray-800/50' : 'border-gray-200 bg-white'}`
                                }`}
                        >
                            {session.is_current && (
                                <span className="inline-block text-xs bg-emerald-500 text-white px-2 py-1 rounded mb-3">
                                    ✓ This Device
                                </span>
                            )}

                            <div className="flex items-start gap-4">
                                <div className={`p-3 rounded-lg ${isDarkMode ? 'bg-gray-700' : 'bg-gray-100'}`}>
                                    {getDeviceIcon(session.device_type)}
                                </div>

                                <div className="flex-1 min-w-0">
                                    <p className={`font-semibold truncate ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
                                        {session.device_name || 'Unknown Device'}
                                    </p>
                                    <p className={`text-sm ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                                        {session.browser} • {session.os}
                                    </p>

                                    <div className={`flex items-center gap-1 mt-2 text-xs ${isDarkMode ? 'text-gray-500' : 'text-gray-500'}`}>
                                        <MapPin className="w-3 h-3" />
                                        <span>{session.location || 'Unknown'}</span>
                                    </div>

                                    <div className={`flex items-center gap-1 mt-1 text-xs ${isDarkMode ? 'text-gray-500' : 'text-gray-500'}`}>
                                        <Clock className="w-3 h-3" />
                                        <span>Last active {formatRelativeTime(session.last_used_at)}</span>
                                    </div>

                                    <p className={`text-xs mt-1 ${isDarkMode ? 'text-gray-600' : 'text-gray-400'}`}>
                                        IP: {session.ip_address}
                                    </p>
                                </div>
                            </div>

                            {!session.is_current && (
                                <button
                                    onClick={() => handleRevokeSession(session.id)}
                                    disabled={revoking === session.id}
                                    className={`mt-4 w-full py-2 rounded-lg font-medium transition-colors ${isDarkMode
                                        ? 'bg-red-500/10 text-red-400 hover:bg-red-500/20'
                                        : 'bg-red-50 text-red-600 hover:bg-red-100'
                                        } disabled:opacity-50 disabled:cursor-not-allowed`}
                                >
                                    {revoking === session.id ? 'Revoking...' : 'Revoke Session'}
                                </button>
                            )}
                        </div>
                    ))}
                </div>

                {activeSessions.length > 1 && (
                    <button
                        onClick={handleLogoutAllDevices}
                        className="bg-red-500 text-white px-6 py-3 rounded-lg font-semibold hover:bg-red-600 transition-colors"
                    >
                        Logout from All Other Devices
                    </button>
                )}
            </div>

            {/* Login History */}
            <div className="space-y-4">
                <div>
                    <h2 className={`text-2xl font-bold ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
                        Login History
                    </h2>
                    <p className={`text-sm mt-1 ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                        Recent login attempts to your account
                    </p>
                </div>

                <div className={`rounded-lg border overflow-hidden ${isDarkMode ? 'border-gray-700' : 'border-gray-200'}`}>
                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead className={isDarkMode ? 'bg-gray-800' : 'bg-gray-50'}>
                                <tr>
                                    <th className={`px-4 py-3 text-left text-xs font-medium ${isDarkMode ? 'text-gray-400' : 'text-gray-600'} uppercase`}>
                                        Date & Time
                                    </th>
                                    <th className={`px-4 py-3 text-left text-xs font-medium ${isDarkMode ? 'text-gray-400' : 'text-gray-600'} uppercase`}>
                                        Device
                                    </th>
                                    <th className={`px-4 py-3 text-left text-xs font-medium ${isDarkMode ? 'text-gray-400' : 'text-gray-600'} uppercase`}>
                                        Location
                                    </th>
                                    <th className={`px-4 py-3 text-left text-xs font-medium ${isDarkMode ? 'text-gray-400' : 'text-gray-600'} uppercase`}>
                                        IP Address
                                    </th>
                                    <th className={`px-4 py-3 text-left text-xs font-medium ${isDarkMode ? 'text-gray-400' : 'text-gray-600'} uppercase`}>
                                        Status
                                    </th>
                                </tr>
                            </thead>
                            <tbody className={`divide-y ${isDarkMode ? 'divide-gray-700' : 'divide-gray-200'} `}>
                                {loginHistory.map((entry, idx) => (
                                    <tr key={idx} className={isDarkMode ? 'bg-gray-800/30' : 'bg-white'}>
                                        <td className={`px-4 py-3 text-sm ${isDarkMode ? 'text-gray-300' : 'text-gray-900'}`}>
                                            {formatDateTime(entry.login_time)}
                                        </td>
                                        <td className="px-4 py-3">
                                            <div className="flex items-center gap-2">
                                                {getDeviceIcon(entry.device_type)}
                                                <div>
                                                    <p className={`text-sm font-medium ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
                                                        {entry.device_name}
                                                    </p>
                                                    <p className={`text-xs ${isDarkMode ? 'text-gray-500' : 'text-gray-500'}`}>
                                                        {entry.browser} • {entry.os}
                                                    </p>
                                                </div>
                                            </div>
                                        </td>
                                        <td className={`px-4 py-3 text-sm ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                                            {entry.location || 'Unknown'}
                                        </td>
                                        <td className={`px-4 py-3 text-sm font-mono ${isDarkMode ? 'text-gray-500' : 'text-gray-500'}`}>
                                            {entry.ip_address}
                                        </td>
                                        <td className="px-4 py-3">
                                            {entry.login_success ? (
                                                <span className="inline-flex items-center gap-1 text-emerald-500 text-sm font-medium">
                                                    <CheckCircle2 className="w-4 h-4" />
                                                    Success
                                                </span>
                                            ) : (
                                                <div>
                                                    <span className="inline-flex items-center gap-1 text-red-500 text-sm font-medium">
                                                        <XCircle className="w-4 h-4" />
                                                        Failed
                                                    </span>
                                                    {entry.failure_reason && (
                                                        <p className={`text-xs mt-1 ${isDarkMode ? 'text-gray-500' : 'text-gray-500'}`}>
                                                            {entry.failure_reason}
                                                        </p>
                                                    )}
                                                </div>
                                            )}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>

                {loginHistory.length === 0 && (
                    <div className={`text-center py-8 ${isDarkMode ? 'text-gray-500' : 'text-gray-400'}`}>
                        No login history available
                    </div>
                )}
            </div>
        </div>
    );
}
