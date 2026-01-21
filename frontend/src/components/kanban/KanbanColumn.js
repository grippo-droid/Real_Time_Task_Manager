// src/components/kanban/KanbanColumn.js
import React from 'react';
import { useDroppable } from '@dnd-kit/core';
import { SortableContext, verticalListSortingStrategy } from '@dnd-kit/sortable';
import { SortableTask } from './SortableTask';

export const KanbanColumn = ({ id, title, tasks, currentUserId }) => {
    const { setNodeRef } = useDroppable({ id });

    return (
        <div className="bg-gray-100 dark:bg-gray-800 rounded-lg p-4 min-w-[300px] flex flex-col h-full">
            <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-gray-900 dark:text-white capitalize">
                    {title.replace('_', ' ')}
                </h3>
                <span className="bg-white dark:bg-gray-700 px-2 py-1 rounded-full text-sm font-medium text-gray-600 dark:text-gray-300">
                    {tasks.length}
                </span>
            </div>

            <div ref={setNodeRef} className="flex-1 overflow-y-auto min-h-[100px]">
                <SortableContext
                    id={id}
                    items={tasks.map(t => t.id)}
                    strategy={verticalListSortingStrategy}
                >
                    {tasks.map((task) => (
                        <SortableTask
                            key={task.id}
                            task={task}
                            currentUserId={currentUserId}
                        />
                    ))}
                </SortableContext>
                {/* Placeholder for dropping if empty, styled transparently */}
                {tasks.length === 0 && (
                    <div className="h-full w-full flex items-center justify-center text-gray-400 text-sm border-2 border-dashed border-gray-300 rounded">
                        Drop here
                    </div>
                )}
            </div>
        </div>
    );
};
