import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { usersAPI } from '../services/api';
import { Avatar } from '../components/Avatar';
import { ThemeToggle } from '../components/ThemeToggle';
import { ArrowLeft, Save, User, Camera } from 'lucide-react';
import toast from 'react-hot-toast';
import { useNavigate } from 'react-router-dom';

export const ProfileSettings = () => {
    const { user } = useAuth(); // We might need a way to update user in context
    const navigate = useNavigate();
    const [loading, setLoading] = useState(false);

    // State
    const [avatarUrl, setAvatarUrl] = useState(user?.avatar_url || '');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');

    const handleSubmit = async (e) => {
        e.preventDefault();

        if (password && password !== confirmPassword) {
            toast.error("Passwords don't match");
            return;
        }

        setLoading(true);
        try {
            const updates = {};
            if (avatarUrl !== user.avatar_url) updates.avatar_url = avatarUrl;
            if (password) updates.password = password;

            if (Object.keys(updates).length === 0) {
                toast("No changes to save");
                setLoading(false);
                return;
            }

            const response = await usersAPI.updateProfile(updates);

            // Hacky: Update local storage user manually or define a refetchUser in AuthContext
            // Ideally AuthContext should export a function to update the user state directly
            // For now, we will manually update localStorage and reload to be safe or just trigger a re-login flow?
            // Better: update user context.
            // Let's assume we can just update the context if we exposed a setter, 
            // but for now let's just show success and maybe simple reload or relying on next fetch.
            // Actually, we should really update the context.
            // But since 'login' sets the user, we can simulate it if we had the token.

            // Simplest: Update localStorage and reload page to reflect changes in Context
            const updatedUser = response.data;
            localStorage.setItem('user', JSON.stringify(updatedUser));

            toast.success('Profile updated! Refreshing...');
            setTimeout(() => window.location.reload(), 1000);

        } catch (error) {
            toast.error(error.response?.data?.detail || 'Failed to update profile');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors duration-200">
            <header className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
                <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                            <button
                                onClick={() => navigate(-1)}
                                className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition"
                            >
                                <ArrowLeft className="w-5 h-5 text-gray-600 dark:text-gray-300" />
                            </button>
                            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Profile Settings</h1>
                        </div>
                        <ThemeToggle />
                    </div>
                </div>
            </header>

            <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg overflow-hidden border border-gray-100 dark:border-gray-700">
                    <div className="p-8">
                        <form onSubmit={handleSubmit} className="space-y-8">

                            {/* Avatar Section */}
                            <div className="space-y-4">
                                <h3 className="text-lg font-medium text-gray-900 dark:text-white flex items-center gap-2">
                                    <Camera className="w-5 h-5" /> Avatar
                                </h3>
                                <div className="flex flex-col sm:flex-row items-center gap-6">
                                    <div className="relative group">
                                        <Avatar user={{ ...user, avatar_url: avatarUrl }} size="xl" />
                                    </div>
                                    <div className="flex-1 w-full">
                                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                            Avatar URL
                                        </label>
                                        <div className="flex gap-2">
                                            <input
                                                type="url"
                                                value={avatarUrl}
                                                onChange={(e) => setAvatarUrl(e.target.value)}
                                                placeholder="https://example.com/avatar.jpg"
                                                className="flex-1 px-4 py-2 bg-gray-50 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 dark:text-white transition-all"
                                            />
                                            <button
                                                type="button"
                                                onClick={() => setAvatarUrl('')}
                                                className="px-4 py-2 text-sm text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg border border-gray-300 dark:border-gray-600"
                                            >
                                                Reset
                                            </button>
                                        </div>
                                        <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">
                                            Leave empty to use a generated avatar based on your username.
                                        </p>
                                    </div>
                                </div>
                            </div>

                            <hr className="border-gray-200 dark:border-gray-700" />

                            {/* Credentials Section */}
                            <div className="space-y-4">
                                <h3 className="text-lg font-medium text-gray-900 dark:text-white flex items-center gap-2">
                                    <User className="w-5 h-5" /> Account Details
                                </h3>

                                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                            Username
                                        </label>
                                        <input
                                            type="text"
                                            value={user?.username || ''}
                                            disabled
                                            className="w-full px-4 py-2 bg-gray-100 dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-500 dark:text-gray-400 cursor-not-allowed"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                            Email
                                        </label>
                                        <input
                                            type="email"
                                            value={user?.email || ''}
                                            disabled
                                            className="w-full px-4 py-2 bg-gray-100 dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-500 dark:text-gray-400 cursor-not-allowed"
                                        />
                                    </div>
                                </div>

                                <div className="pt-4">
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                        New Password (Optional)
                                    </label>
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                        <input
                                            type="password"
                                            value={password}
                                            onChange={(e) => setPassword(e.target.value)}
                                            placeholder="New password"
                                            className="w-full px-4 py-2 bg-gray-50 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 dark:text-white"
                                        />
                                        <input
                                            type="password"
                                            value={confirmPassword}
                                            onChange={(e) => setConfirmPassword(e.target.value)}
                                            placeholder="Confirm new password"
                                            className="w-full px-4 py-2 bg-gray-50 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 dark:text-white"
                                        />
                                    </div>
                                </div>
                            </div>

                            {/* Submit Button */}
                            <div className="flex justify-end pt-4">
                                <button
                                    type="submit"
                                    disabled={loading}
                                    className="flex items-center gap-2 px-8 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 focus:ring-4 focus:ring-indigo-500/30 transition-all disabled:opacity-50 disabled:cursor-not-allowed font-medium shadow-md shadow-indigo-600/20"
                                >
                                    {loading ? (
                                        <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                                    ) : (
                                        <>
                                            <Save className="w-5 h-5" /> Save Changes
                                        </>
                                    )}
                                </button>
                            </div>

                        </form>
                    </div>
                </div>
            </main>
        </div>
    );
};
