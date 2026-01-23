import React from 'react';
import { X, Calendar, Clock } from 'lucide-react';
import { Avatar } from '../Avatar';
import { format } from 'date-fns';
import { CommentSection } from './CommentSection';
import { AttachmentSection } from './AttachmentSection';

export const TaskDetailModal = ({ task, isOpen, onClose, currentUserId }) => {
    if (!isOpen || !task) return null;

    // We will add state for comments and attachments later

    return (
        <div className="fixed inset-0 z-50 overflow-y-auto" aria-labelledby="modal-title" role="dialog" aria-modal="true">
            {/* Backdrop */}
            <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
                <div
                    className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"
                    aria-hidden="true"
                    onClick={onClose}
                ></div>

                <span className="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">&#8203;</span>

                {/* Modal Panel */}
                <div className="inline-block align-bottom bg-white dark:bg-gray-800 rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-2xl sm:w-full">

                    {/* Header */}
                    <div className="px-4 pt-5 pb-4 sm:p-6 sm:pb-4 border-b border-gray-200 dark:border-gray-700">
                        <div className="flex justify-between items-start">
                            <h3 className="text-xl leading-6 font-medium text-gray-900 dark:text-white" id="modal-title">
                                {task.title}
                            </h3>
                            <button
                                onClick={onClose}
                                className="bg-white dark:bg-gray-800 rounded-md text-gray-400 hover:text-gray-500 focus:outline-none"
                            >
                                <X className="h-6 w-6" />
                            </button>
                        </div>
                        <div className="mt-2 flex items-center gap-4 text-sm text-gray-500 dark:text-gray-400">
                            <span className="flex items-center gap-1">
                                <span className={`w-2.5 h-2.5 rounded-full ${task.status === 'completed' ? 'bg-green-500' :
                                    task.status === 'in_progress' ? 'bg-blue-500' :
                                        'bg-gray-500'
                                    }`}></span>
                                {task.status.replace('_', ' ')}
                            </span>
                            <span className={`px-2 py-0.5 rounded text-xs font-medium ${task.priority === 'urgent' ? 'bg-red-100 text-red-700' :
                                task.priority === 'high' ? 'bg-orange-100 text-orange-700' :
                                    'bg-gray-100 text-gray-700'
                                }`}>
                                {task.priority}
                            </span>
                        </div>
                    </div>

                    {/* Content */}
                    <div className="px-4 py-5 sm:p-6">
                        {/* Description */}
                        <div className="mb-6">
                            <h4 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">Description</h4>
                            <p className="text-sm text-gray-900 dark:text-gray-300 whitespace-pre-wrap">
                                {task.description || "No description provided."}
                            </p>
                        </div>

                        {/* Validated Details */}
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-8">
                            <div>
                                <h4 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">Assignee</h4>
                                <div className="flex items-center gap-2">
                                    {task.assigned_to ? (
                                        <>
                                            <Avatar user={{ username: task.assigned_to }} size="sm" />
                                            <span className="text-sm text-gray-900 dark:text-white">
                                                {task.assigned_to === currentUserId ? 'You' : `User ${task.assigned_to.substr(0, 4)}...`}
                                            </span>
                                        </>
                                    ) : (
                                        <span className="text-sm text-gray-500 italic">Unassigned</span>
                                    )}
                                </div>
                            </div>
                            <div>
                                <h4 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">Details</h4>
                                <div className="space-y-1">
                                    <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-300">
                                        <Calendar className="w-4 h-4" />
                                        <span>Created {task.created_at ? format(new Date(task.created_at), 'MMM d, yyyy') : 'Recently'}</span>
                                    </div>
                                    {task.due_date && (
                                        <div className="flex items-center gap-2 text-sm text-red-600">
                                            <Clock className="w-4 h-4" />
                                            <span>Due {format(new Date(task.due_date), 'MMM d, yyyy')}</span>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>

                        {/* Comments & Attachments */}
                        <div className="border-t border-gray-200 dark:border-gray-700 pt-6">
                            <AttachmentSection taskId={task.id} />
                            <CommentSection taskId={task.id} currentUserId={currentUserId} />
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};
