'use client';
import { useState } from 'react';

interface FeedbackBarProps {
  feedItemId: string;
  onFeedback: (action: string, comment?: string) => void;
}

export default function FeedbackBar({ feedItemId, onFeedback }: FeedbackBarProps) {
  const [showComment, setShowComment] = useState(false);
  const [comment, setComment] = useState('');

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center gap-2">
        {['like', 'dislike', 'more_like_this', 'less_like_this', 'too_basic', 'too_advanced'].map(
          (action) => (
            <button
              key={action}
              onClick={() => onFeedback(action)}
              className="text-xs px-2 py-1 rounded bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700"
            >
              {action.replace(/_/g, ' ')}
            </button>
          )
        )}
        <button
          onClick={() => setShowComment(!showComment)}
          className="text-xs px-2 py-1 rounded bg-gray-100 dark:bg-gray-800"
        >
          💬
        </button>
      </div>
      {showComment && (
        <div className="flex gap-2">
          <input
            type="text"
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            placeholder="Your feedback..."
            className="flex-1 text-sm px-3 py-1 border rounded"
          />
          <button
            onClick={() => {
              onFeedback('comment', comment);
              setComment('');
              setShowComment(false);
            }}
            className="text-xs px-3 py-1 bg-blue-500 text-white rounded"
          >
            Send
          </button>
        </div>
      )}
    </div>
  );
}
