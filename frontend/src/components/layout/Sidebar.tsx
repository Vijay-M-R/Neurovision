import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Upload,
  Brain,
  Eye,
  Sparkles,
  FileText,
  CheckCircle2,
  Lock,
} from 'lucide-react';
import { useAppStore } from '../../store/useAppStore';

interface NavItem {
  name: string;
  path: string;
  icon: React.ElementType;
  requiresJob?: boolean;
  requiresSegmentation?: boolean;
}

const navItems: NavItem[] = [
  { name: 'Dashboard', path: '/', icon: LayoutDashboard },
  { name: 'Upload MRI', path: '/upload', icon: Upload },
  { name: 'AI Segmentation', path: '/processing', icon: Brain, requiresJob: true },
  { name: '3-View Viewer', path: '/visualization', icon: Eye, requiresJob: true, requiresSegmentation: true },
  { name: 'Enhancement', path: '/enhancement', icon: Sparkles, requiresJob: true },
  { name: 'Clinical Results', path: '/results', icon: FileText, requiresJob: true, requiresSegmentation: true },
];

export const Sidebar: React.FC = () => {
  const { currentJobId, segmentResult, resultRecord } = useAppStore();

  const hasJob = Boolean(currentJobId);
  const hasSegmentation = Boolean(segmentResult || resultRecord);

  return (
    <aside className="w-64 bg-[#0d131f] border-r border-panelBorder flex flex-col shrink-0">
      {/* Workstation Workspace Title */}
      <div className="p-4 border-b border-panelBorder/60">
        <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400">
          Workstation Workspace
        </div>
        <div className="text-xs text-slate-300 font-medium mt-0.5">
          Brain MRI Clinical Tool
        </div>
      </div>

      {/* Navigation links */}
      <nav className="flex-1 p-3 space-y-1.5 overflow-y-auto">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isLocked = (item.requiresJob && !hasJob) || (item.requiresSegmentation && !hasSegmentation);

          if (isLocked) {
            return (
              <div
                key={item.path}
                title={item.requiresSegmentation ? 'Requires completed AI segmentation' : 'Requires uploaded MRI scan'}
                className="flex items-center justify-between px-3.5 py-2.5 rounded-lg text-xs font-medium text-slate-500 cursor-not-allowed bg-slate-900/40 select-none opacity-60"
              >
                <div className="flex items-center gap-3">
                  <Icon className="w-4 h-4 text-slate-500" />
                  <span>{item.name}</span>
                </div>
                <Lock className="w-3.5 h-3.5 text-slate-600" />
              </div>
            );
          }

          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `flex items-center justify-between px-3.5 py-2.5 rounded-lg text-xs font-medium transition-all ${
                  isActive
                    ? 'bg-cyan-950/70 border border-cyan-800/80 text-cyan-300 font-semibold shadow-sm'
                    : 'text-slate-300 hover:bg-slate-800/60 hover:text-slate-100 border border-transparent'
                }`
              }
            >
              <div className="flex items-center gap-3">
                <Icon className="w-4 h-4 text-cyan-400" />
                <span>{item.name}</span>
              </div>
              {item.requiresSegmentation && hasSegmentation && (
                <CheckCircle2 className="w-3.5 h-3.5 text-teal-400" />
              )}
            </NavLink>
          );
        })}
      </nav>

      {/* Session Information Box */}
      <div className="p-4 border-t border-panelBorder/80 bg-slate-900/50">
        <div className="text-[11px] font-mono text-slate-400 mb-1">SESSION STATUS</div>
        <div className="space-y-1 text-[11px]">
          <div className="flex justify-between text-slate-300">
            <span>MRI Scan:</span>
            <span className={hasJob ? 'text-teal-400 font-mono' : 'text-slate-500'}>
              {hasJob ? 'Loaded' : 'None'}
            </span>
          </div>
          <div className="flex justify-between text-slate-300">
            <span>Segmentation:</span>
            <span className={hasSegmentation ? 'text-teal-400 font-mono' : 'text-slate-500'}>
              {hasSegmentation ? 'Ready' : 'Pending'}
            </span>
          </div>
        </div>
      </div>
    </aside>
  );
};
