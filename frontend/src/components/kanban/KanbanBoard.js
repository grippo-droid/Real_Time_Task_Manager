// src/components/kanban/KanbanBoard.js
import React, { useState } from 'react';
import {
    DndContext,
    closestCorners,
    KeyboardSensor,
    PointerSensor,
    useSensor,
    useSensors,
    DragOverlay,
} from '@dnd-kit/core';
import { sortableKeyboardCoordinates } from '@dnd-kit/sortable';
import { KanbanColumn } from './KanbanColumn';
import { SortableTask } from './SortableTask';

const COLUMNS = ['todo', 'in_progress', 'review', 'completed'];

export const KanbanBoard = ({ tasks, onTaskDrop, currentUserId }) => {
    const [activeId, setActiveId] = useState(null);

    const sensors = useSensors(
        useSensor(PointerSensor, {
            activationConstraint: {
                distance: 8, // Require movement of 8px to start drag (prevents accidental drag on click)
            },
        }),
        useSensor(KeyboardSensor, {
            coordinateGetter: sortableKeyboardCoordinates,
        })
    );

    const handleDragStart = (event) => {
        setActiveId(event.active.id);
    };

    const handleDragEnd = (event) => {
        const { active, over } = event;
        setActiveId(null);

        if (!over) return;

        const taskId = active.id;
        // 'over.id' could be a column ID ('todo') or another task ID.
        // If it's a task ID, we need to find which column that task belongs to, 
        // BUT for simplicity in this MVP, we will rely on droppable columns.
        // Actually, with SortableContext, 'over' might be the sortable item.
        // Dnd-kit logic: if dropping over a container (column), over.id is column id.
        // If dropping over an item in a container, over.id is that item's id.

        // We need to determine the destination status.
        let newStatus = null;

        if (COLUMNS.includes(over.id)) {
            newStatus = over.id;
        } else {
            // If dropped over a task, find that task's status
            const overTask = tasks.find(t => t.id === over.id);
            if (overTask) {
                newStatus = overTask.status;
            }
        }

        if (newStatus) {
            // Find the dragged task
            const activeTask = tasks.find(t => t.id === taskId);
            if (activeTask && activeTask.status !== newStatus) {
                onTaskDrop(taskId, newStatus);
            }
        }
    };

    // Group tasks by status
    const tasksByStatus = COLUMNS.reduce((acc, status) => {
        acc[status] = tasks.filter(t => t.status === status);
        return acc;
    }, {});

    // Find active task for overlay
    const activeTask = activeId ? tasks.find(t => t.id === activeId) : null;

    return (
        <DndContext
            sensors={sensors}
            collisionDetection={closestCorners}
            onDragStart={handleDragStart}
            onDragEnd={handleDragEnd}
        >
            <div className="flex-1 overflow-x-auto p-4 sm:p-6 lg:p-8 h-full">
                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6 min-w-max h-full items-start">
                    {COLUMNS.map((status) => (
                        <KanbanColumn
                            key={status}
                            id={status}
                            title={status}
                            tasks={tasksByStatus[status]}
                            currentUserId={currentUserId}
                        />
                    ))}
                </div>
            </div>

            <DragOverlay>
                {activeTask ? (
                    <div className="opacity-90 rotate-2 scale-105 cursor-grabbing">
                        <SortableTask task={activeTask} currentUserId={currentUserId} />
                    </div>
                ) : null}
            </DragOverlay>
        </DndContext>
    );
};
