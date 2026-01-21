import React from 'react';

export const Avatar = ({ user, size = 'sm', className = '' }) => {
    // Generate DiceBear URL based on username if no custom avatar is set
    // Using user.username as seed ensures consistency
    const getAvatarUrl = () => {
        if (user?.avatar_url) return user.avatar_url;
        const seed = user?.username || 'user';
        return `https://api.dicebear.com/7.x/avataaars/svg?seed=${seed}&backgroundColor=b6e3f4,c0aede,d1d4f9`;
    };

    const sizeClasses = {
        xs: 'w-6 h-6',
        sm: 'w-8 h-8',
        md: 'w-10 h-10',
        lg: 'w-16 h-16',
        xl: 'w-24 h-24'
    };

    return (
        <div className={`relative rounded-full overflow-hidden bg-gray-100 ${sizeClasses[size]} ${className}`}>
            <img
                src={getAvatarUrl()}
                alt={`${user?.username}'s avatar`}
                className="w-full h-full object-cover"
                onError={(e) => {
                    // Fallback to initial if image fails
                    e.target.style.display = 'none';
                    e.target.nextSibling.style.display = 'flex';
                }}
            />
            {/* Fallback Initial */}
            <div className="hidden absolute inset-0 items-center justify-center bg-indigo-100 text-indigo-600 font-bold uppercase" style={{ display: 'none' }}>
                {user?.username?.charAt(0) || '?'}
            </div>
        </div>
    );
};
