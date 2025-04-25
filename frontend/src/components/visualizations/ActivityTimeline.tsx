"use client";

import React, { useState, useMemo, useEffect } from 'react';
import { sentinelApi } from '@/lib/apiClient';

interface TimelineEvent {
  id: string;
  timestamp: string | Date;
  type: string;
  title: string;
  description?: string;
  isSuspicious?: boolean;
  severity?: 'low' | 'medium' | 'high';
  amount?: number;
  relatedAddress?: string;
}

interface ActivityTimelineProps {
  events?: TimelineEvent[];
  title?: string;
  showFilters?: boolean;
  highlightSuspicious?: boolean;
  height?: number;
  targetAddress?: string;
  fetchLive?: boolean;
}

const ActivityTimeline: React.FC<ActivityTimelineProps> = ({
  events: initialEvents,
  title = "Activity Timeline",
  showFilters = false,
  highlightSuspicious = true,
  height = 400,
  targetAddress,
  fetchLive = false,
}) => {
  const [filter, setFilter] = useState<string>("all");
  const [showSuspiciousOnly, setShowSuspiciousOnly] = useState<boolean>(false);
  const [events, setEvents] = useState<TimelineEvent[]>(initialEvents || []);
  const [loading, setLoading] = useState<boolean>(fetchLive && !initialEvents);
  const [error, setError] = useState<string | null>(null);

  // Fetch timeline events from the backend if fetchLive is true
  useEffect(() => {
    if (fetchLive || (!initialEvents && targetAddress)) {
      const fetchTimelineEvents = async () => {
        try {
          setLoading(true);
          setError(null);
          
          const response = await sentinelApi.getActivityTimeline(targetAddress);
          
          if (response && Array.isArray(response.events)) {
            setEvents(response.events.map((event: TimelineEvent) => ({
              ...event,
              timestamp: new Date(event.timestamp),
              id: event.id || `event-${Math.random().toString(36).substr(2, 9)}`
            })));
          } else {
            setEvents([]);
            setError("Invalid response format from API");
          }
        } catch (err) {
          console.error("Failed to fetch timeline events:", err);
          setError(err instanceof Error ? err.message : "Failed to fetch timeline data");
          setEvents([]);
        } finally {
          setLoading(false);
        }
      };

      fetchTimelineEvents();
    } else if (initialEvents) {
      setEvents(initialEvents);
    }
  }, [fetchLive, initialEvents, targetAddress]);

  // Sort events by date
  const sortedEvents = useMemo(() => {
    return [...events].sort((a, b) => {
      const dateA = new Date(a.timestamp);
      const dateB = new Date(b.timestamp);
      return dateB.getTime() - dateA.getTime(); // Descending order (newest first)
    });
  }, [events]);

  // Apply filters
  const filteredEvents = useMemo(() => {
    return sortedEvents.filter(event => {
      if (showSuspiciousOnly && !event.isSuspicious) {
        return false;
      }
      if (filter !== "all" && event.type !== filter) {
        return false;
      }
      return true;
    });
  }, [sortedEvents, filter, showSuspiciousOnly]);

  // Get unique event types for filter dropdown
  const eventTypes = useMemo(() => {
    const types = new Set<string>();
    events.forEach(event => types.add(event.type));
    return Array.from(types);
  }, [events]);

  // Format date for display
  const formatDate = (date: string | Date): string => {
    const d = typeof date === 'string' ? new Date(date) : date;
    return new Intl.DateTimeFormat('en-US', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    }).format(d);
  };

  // Determine event style based on severity/suspiciousness
  const getEventStyle = (event: TimelineEvent) => {
    if (event.isSuspicious && highlightSuspicious) {
      if (event.severity === 'high') {
        return "border-red-500 bg-red-50 dark:bg-red-900/20";
      }
      if (event.severity === 'medium') {
        return "border-yellow-500 bg-yellow-50 dark:bg-yellow-900/20";
      }
      return "border-orange-400 bg-orange-50 dark:bg-orange-900/20";
    }
    return "border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800";
  };

  if (loading) {
    return (
      <div style={{ height }} className="flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-500"></div>
        <span className="ml-2 text-sm text-gray-600 dark:text-gray-400">Loading timeline data...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ height: 'auto' }} className="p-4 text-center">
        <p className="text-red-500 dark:text-red-400">Error: {error}</p>
        <button 
          onClick={() => window.location.reload()}
          className="mt-2 px-3 py-1 text-sm bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          Retry
        </button>
      </div>
    );
  }

  if (!events.length) {
    return (
      <div style={{ height: 'auto' }} className="p-4 text-center">
        <p className="text-gray-500 dark:text-gray-400">No timeline events found</p>
      </div>
    );
  }

  return (
    <div style={{ height }} className="overflow-hidden flex flex-col">
      <div className="p-4 border-b border-gray-200 dark:border-gray-700">
        <h3 className="text-lg font-medium">{title}</h3>
        {showFilters && (
          <div className="flex flex-wrap gap-2 mt-2 items-center">
            <select
              className="px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
            >
              <option value="all">All Events</option>
              {eventTypes.map(type => (
                <option key={type} value={type}>
                  {type.charAt(0).toUpperCase() + type.slice(1)}
                </option>
              ))}
            </select>
            
            <label className="inline-flex items-center text-sm">
              <input
                type="checkbox"
                className="mr-1"
                checked={showSuspiciousOnly}
                onChange={() => setShowSuspiciousOnly(!showSuspiciousOnly)}
              />
              <span>Suspicious only</span>
            </label>
          </div>
        )}
      </div>

      <div className="flex-1 overflow-y-auto p-4">
        {filteredEvents.length === 0 ? (
          <div className="text-center py-8 text-gray-500 dark:text-gray-400">
            No events found for the selected filters
          </div>
        ) : (
          <div className="space-y-4">
            {filteredEvents.map((event) => (
              <div
                key={event.id}
                className={`p-3 border-l-4 rounded shadow-sm ${getEventStyle(event)}`}
              >
                <div className="flex justify-between items-start">
                  <div className="font-medium">{event.title}</div>
                  <div className="text-xs text-gray-500 dark:text-gray-400">
                    {formatDate(event.timestamp)}
                  </div>
                </div>
                {event.description && (
                  <p className="mt-1 text-sm text-gray-600 dark:text-gray-300">
                    {event.description}
                  </p>
                )}
                <div className="mt-1 flex flex-wrap gap-2 text-xs">
                  <span className="px-2 py-0.5 rounded-full bg-gray-100 dark:bg-gray-700">
                    {event.type}
                  </span>
                  {event.isSuspicious && (
                    <span className="px-2 py-0.5 rounded-full bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-300">
                      Suspicious
                    </span>
                  )}
                  {event.amount && (
                    <span className="px-2 py-0.5 rounded-full bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-300">
                      {typeof event.amount === 'number'
                        ? event.amount.toLocaleString() + ' SOL'
                        : event.amount}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default ActivityTimeline;
