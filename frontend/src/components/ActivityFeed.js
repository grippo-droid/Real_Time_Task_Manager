import React, { useEffect, useState } from 'react';
import { activityAPI } from '../services/api';
import {
    Activity,
    CheckCircle,
    Plus,
    Trash2,
    Edit,
    UserPlus,
    ArrowRight,
    Layout
} from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

const ActivityFeed = () => {
    const [activities, setActivities] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadActivity();
    }, []);

    const loadActivity = async () => {
        try {
            const response = await activityAPI.getRecentActivity();
            setActivities(response.data);
        } catch (error) {
            console.error('Failed to load activity feed:', error);
        } finally {
            setLoading(false);
        }
    };

    const getIcon = (action) => {
        switch (action) {
            case 'created_task':
            case 'created_board':
            case 'created_team':
                return <Plus className="w-4 h-4 text-green-500" />;
            case 'completed_task':
                return <CheckCircle className="w-4 h-4 text-green-600" />;
            case 'deleted_task':
            case 'deleted_board':
            case 'deleted_team':
                return <Trash2 className="w-4 h-4 text-red-500" />;
            case 'updated_task':
            case 'updated_task_status':
                return <Edit className="w-4 h-4 text-blue-500" />;
            case 'assigned_task':
                return <UserPlus className="w-4 h-4 text-purple-500" />;
            case 'moved_task':
                return <ArrowRight className="w-4 h-4 text-orange-500" />;
            default:
                return <Activity className="w-4 h-4 text-gray-500" />;
        }
    };

    const getActionText = (activity) => {
        const { action, details, entity_type } = activity;

        // Use details if available as it's more descriptive
        if (details) return details;

        // Fallback text generation
        switch (action) {
            case 'created_task': return `created a new task`;
            case 'updated_task_status': return `updated task status`;
            case 'deleted_task': return `deleted a task`;
            case 'created_board': return `created a new board`;
            default: return `performed ${action} on ${entity_type}`;
        }
    };

    if (loading) {
        return (
            <div className="animate-pulse space-y-4">
                {[1, 2, 3].map((i) => (
                    <div key={i} className="flex gap-4 p-3 border border-gray-100 dark:border-gray-700 rounded-lg">
                        <div className="w-8 h-8 bg-gray-200 dark:bg-gray-700 rounded-full"></div>
                        <div className="flex-1 space-y-2">
                            <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4"></div>
                            <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-1/2"></div>
                        </div>
                    </div>
                ))}
            </div>
        );
    }

    if (activities.length === 0) {
        return (
            <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                <Activity className="w-12 h-12 mx-auto mb-3 opacity-50" />
                <p>No recent activity</p>
            </div>
        );
    }

    return (
        <div className="space-y-4 max-h-[500px] overflow-y-auto pr-2 custom-scrollbar">
            {activities.map((activity) => (
                <div
                    key={activity.id}
                    className="flex gap-3 p-3 bg-white dark:bg-gray-800 border border-gray-100 dark:border-gray-700 rounded-lg hover:shadow-sm transition group"
                >
                    <div className="mt-1 p-2 bg-gray-50 dark:bg-gray-700 rounded-full h-fit group-hover:bg-indigo-50 dark:group-hover:bg-gray-600 transition">
                        {getIcon(activity.action)}
                    </div>
                    <div className="flex-1">
                        <p className="text-sm text-gray-900 dark:text-white">
                            <span className="font-semibold">{activity.username}</span>{' '}
                            <span className="text-gray-600 dark:text-gray-300">
                                {getActionText(activity)}
                            </span>
                        </p>
                        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                            {formatDistanceToNow(new Date(activity.created_at), { addSuffix: true })}
                        </p>
                    </div>
                </div>
            ))}
        </div>
    );
};

export default ActivityFeed;
