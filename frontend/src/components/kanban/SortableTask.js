// src/components/kanban/SortableTask.js
import React from 'react';
import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { Avatar } from '../Avatar';

export const SortableTask = ({ task, currentUserId, onClick }) => {
    const {
        attributes,
        listeners,
        setNodeRef,
        transform,
        transition,
        isDragging,
    } = useSortable({ id: task.id });

    const style = {
        transform: CSS.Translate.toString(transform),
        transition,
        opacity: isDragging ? 0.5 : 1,
    };

    const priorityColors = {
        urgent: 'bg-red-100 text-red-700',
        high: 'bg-orange-100 text-orange-700',
        medium: 'bg-yellow-100 text-yellow-700',
        low: 'bg-gray-100 text-gray-700',
    };

    return (
        <div
            ref={setNodeRef}
            style={style}
            {...attributes}
            {...listeners}
            onClick={onClick}
            className={`bg-white dark:bg-gray-700 rounded-lg p-4 shadow-sm hover:shadow-md transition border-l-4 border-transparent hover:border-indigo-500 cursor-grab active:cursor-grabbing mb-3 touch-none`}
        >
            <h4 className="font-medium text-gray-900 dark:text-white mb-2">{task.title}</h4>
            {task.description && (
                <p className="text-sm text-gray-600 dark:text-gray-300 mb-3 truncate">{task.description}</p>
            )}

            <div className="flex items-center justify-between">
                <span
                    className={`px-2 py-1 text-xs font-medium rounded ${priorityColors[task.priority] || priorityColors.medium
                        }`}
                >
                    {task.priority || 'medium'}
                </span>
                {task.assigned_to && (
                    <div title={`Assigned to ${task.assigned_to === currentUserId ? 'You' : 'User ' + task.assigned_to.substr(0, 4)}`}>
                        <Avatar user={{ username: task.assigned_to }} size="xs" />
                    </div>
                )}
            </div>
        </div>
    );
};
