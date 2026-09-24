import { useEffect, useRef, useState } from "react";
import { notificationsService } from "../services/applications";
import { timeAgo } from "../utils/format";

export default function NotificationsBell() {
  const [notifications, setNotifications] = useState([]);
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  const load = () => notificationsService.list().then(setNotifications).catch(() => {});

  useEffect(() => {
    load();
    // Polling, not a websocket -- real-time push is out of scope for the
    // MVP (Phase 0 deferred it), and a 30s interval is a reasonable
    // middle ground between "instant" and "never".
    const interval = setInterval(load, 30000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const unreadCount = notifications.filter((n) => !n.is_read).length;

  const markRead = async (id) => {
    await notificationsService.markRead(id);
    load();
  };

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen((o) => !o)}
        className="relative grid place-items-center h-9 w-9 rounded-lg text-ink-700 hover:bg-violet-50 hover:text-violet-700 transition-colors"
        aria-label="Notifications"
      >
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M18 8a6 6 0 0 0-12 0c0 7-3 9-3 9h18s-3-2-3-9" />
          <path d="M13.73 21a2 2 0 0 1-3.46 0" />
        </svg>
        {unreadCount > 0 && (
          <span className="absolute top-0.5 right-0.5 h-4 w-4 rounded-full bg-gradient-to-br from-amber-400 to-amber-500 text-white text-[10px] font-bold flex items-center justify-center ring-2 ring-white animate-pop">
            {unreadCount > 9 ? "9+" : unreadCount}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 mt-2 w-80 bg-white border border-violet-100 rounded-2xl shadow-lift overflow-hidden z-20 animate-pop origin-top-right">
          <div className="px-4 py-3 border-b border-violet-50">
            <p className="font-display font-bold text-sm text-ink-950">Notifications</p>
          </div>
          <div className="max-h-96 overflow-y-auto">
            {notifications.length === 0 && (
              <p className="text-sm text-ink-500 p-6 text-center">No notifications yet.</p>
            )}
            {notifications.map((n) => (
              <button
                key={n.id}
                onClick={() => !n.is_read && markRead(n.id)}
                className={`block w-full text-left px-4 py-3 border-b border-violet-50 last:border-0 hover:bg-violet-50/60 transition-colors ${
                  n.is_read ? "" : "bg-violet-50/40"
                }`}
              >
                <div className="flex items-start gap-2">
                  {!n.is_read && <span className="mt-1.5 h-1.5 w-1.5 rounded-full bg-violet-500 shrink-0" />}
                  <div className="min-w-0">
                    <p className="text-sm font-semibold text-ink-950">{n.title}</p>
                    <p className="text-sm text-ink-500 mt-0.5">{n.message}</p>
                    <p className="text-xs text-ink-500/70 mt-1">{timeAgo(n.created_at)}</p>
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
