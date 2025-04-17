import React, { useState, useEffect } from 'react';
import { Calendar, ChevronDown, BarChart3, Settings, Clock, PieChart, User, LogOut, Home } from 'lucide-react';

const DashboardRedesign = () => {
  const [activePage, setActivePage] = useState('dashboard');
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  
  // Live dashboard data
  const [yearProgress, setYearProgress] = useState(null);
  const [monthProgress, setMonthProgress] = useState(null);
  const [recentDays, setRecentDays] = useState([]);
  const [annualGoal, setAnnualGoal] = useState(null);
  const [monthActual, setMonthActual] = useState(null);
  const [monthTarget, setMonthTarget] = useState(null);
  const [yearActual, setYearActual] = useState(null);
  const [yearTarget, setYearTarget] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    setLoading(true);
    fetch('/planner/api/dashboard', { credentials: 'include' })
      .then(res => {
        if (!res.ok) throw new Error('Failed to fetch dashboard data');
        return res.json();
      })
      .then(data => {
        setYearProgress(data.yearProgress);
        setMonthProgress(data.monthProgress);
        setRecentDays(data.recentDays || []);
        setAnnualGoal(data.annualGoal);
        setMonthActual(data.monthActual);
        setMonthTarget(data.monthTarget);
        setYearActual(data.yearActual);
        setYearTarget(data.yearTarget);
        setLoading(false);
      })
      .catch(err => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return <div className="flex items-center justify-center h-screen text-xl">Loading dashboard...</div>;
  }

  if (error) {
    return <div className="flex items-center justify-center h-screen text-red-600 text-xl">{error}</div>;
  }
  
  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <div className={`bg-slate-800 text-white transition-all duration-300 ${sidebarCollapsed ? 'w-16' : 'w-64'}`}>
        <div className="p-4 flex items-center justify-between">
          {!sidebarCollapsed && <h2 className="text-xl font-bold">BillableHours</h2>}
          <button 
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            className="p-1 rounded-full hover:bg-slate-700"
          >
            <ChevronDown className={`transition-all duration-300 ${sidebarCollapsed ? 'rotate-90' : '-rotate-90'}`} size={20} />
          </button>
        </div>
        
        <nav className="mt-6">
          <NavItem 
            icon={<Home size={20} />} 
            label="Dashboard" 
            active={activePage === 'dashboard'} 
            collapsed={sidebarCollapsed}
            onClick={() => setActivePage('dashboard')}
          />
          <NavItem 
            icon={<Calendar size={20} />} 
            label="Calendar" 
            active={activePage === 'calendar'} 
            collapsed={sidebarCollapsed}
            onClick={() => setActivePage('calendar')}
          />
          <NavItem 
            icon={<Clock size={20} />} 
            label="Time Tracker" 
            active={activePage === 'tracker'} 
            collapsed={sidebarCollapsed}
            onClick={() => setActivePage('tracker')}
          />
          <NavItem 
            icon={<BarChart3 size={20} />} 
            label="Reports" 
            active={activePage === 'reports'} 
            collapsed={sidebarCollapsed}
            onClick={() => setActivePage('reports')}
          />
          <NavItem 
            icon={<Settings size={20} />} 
            label="Settings" 
            active={activePage === 'settings'} 
            collapsed={sidebarCollapsed}
            onClick={() => setActivePage('settings')}
          />
          
          <div className="border-t border-slate-700 my-4"></div>
          
          <NavItem 
            icon={<User size={20} />} 
            label="Profile" 
            active={activePage === 'profile'} 
            collapsed={sidebarCollapsed}
            onClick={() => setActivePage('profile')}
          />
          <NavItem 
            icon={<LogOut size={20} />} 
            label="Logout" 
            collapsed={sidebarCollapsed}
            onClick={() => {}}
          />
        </nav>
      </div>
      
      {/* Main Content */}
      <div className="flex-1 overflow-auto">
        {/* Header */}
        <header className="bg-white shadow-sm p-4">
          <div className="flex justify-between items-center">
            <h1 className="text-2xl font-bold text-gray-800">Dashboard</h1>
            <div className="flex items-center space-x-4">
              <div className="relative">
                <button className="bg-blue-50 text-blue-800 px-4 py-2 rounded-lg font-medium flex items-center space-x-2">
                  <span>April 2025</span>
                  <ChevronDown size={16} />
                </button>
              </div>
              <div className="h-8 w-8 rounded-full bg-blue-600 text-white flex items-center justify-center font-bold">
                JD
              </div>
            </div>
          </div>
        </header>
        
        {/* Dashboard Content */}
        <main className="p-6">
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
            <SummaryCard 
              title="Annual Goal" 
              value="1,800" 
              subvalue="hours" 
              progress={yearProgress} 
              detail={`${yearProgress}% complete`} 
            />
            <SummaryCard 
              title="This Month" 
              value="145" 
              subvalue="of 150 hours" 
              progress={monthProgress} 
              detail="5 hours remaining"
            />
            <SummaryCard 
              title="Daily Average" 
              value="7.8" 
              subvalue="hours/day" 
              colorClass="bg-emerald-500"
              detail="+0.3 from last month"
            />
            <SummaryCard 
              title="Pace Status" 
              value="12.5" 
              subvalue="hours ahead" 
              colorClass="bg-emerald-500"
              detail="On track for annual goal"
            />
          </div>
          
          {/* Recent Activity and Quick Log */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
            <div className="lg:col-span-2 bg-white rounded-xl shadow-sm p-6">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-semibold text-gray-800">Recent Activity</h3>
                <button className="text-blue-600 text-sm font-medium">View All</button>
              </div>
              <div className="space-y-4">
                {recentDays.map((day, index) => (
                  <div key={index} className="flex items-center justify-between border-b border-gray-100 pb-4">
                    <div>
                      <div className="font-medium">{day.date}</div>
                      <div className="text-sm text-gray-500">Target: {day.target} hours</div>
                    </div>
                    <div className="flex items-center">
                      <div className={`px-3 py-1 rounded-lg mr-3 text-sm font-medium ${
                        day.status === 'success' ? 'bg-green-100 text-green-800' :
                        day.status === 'warning' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-blue-100 text-blue-800'
                      }`}>
                        {day.logged} hrs
                      </div>
                      <button className="text-blue-600 hover:text-blue-800">Edit</button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
            
            <div className="bg-white rounded-xl shadow-sm p-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-4">Quick Log Hours</h3>
              <form className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Date</label>
                  <input 
                    type="date" 
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    defaultValue="2025-04-17"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Hours</label>
                  <input 
                    type="number" 
                    step="0.1" 
                    min="0" 
                    max="24"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Enter hours"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Notes (optional)</label>
                  <textarea 
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    rows="2"
                    placeholder="Client or matter reference..."
                  ></textarea>
                </div>
                <button 
                  type="submit" 
                  className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg transition-colors"
                >
                  Log Hours
                </button>
              </form>
            </div>
          </div>
          
          {/* Charts */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
            <div className="bg-white rounded-xl shadow-sm p-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-4">Monthly Progress</h3>
              <div className="h-64 flex items-center justify-center text-gray-400">
                <BarChart3 size={64} />
              </div>
            </div>
            <div className="bg-white rounded-xl shadow-sm p-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-4">Hours by Weekday</h3>
              <div className="h-64 flex items-center justify-center text-gray-400">
                <PieChart size={64} />
              </div>
            </div>
          </div>
          
          {/* Calendar Preview */}
          <div className="bg-white rounded-xl shadow-sm p-6">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold text-gray-800">April 2025</h3>
              <button className="text-blue-600 text-sm font-medium">View Full Calendar</button>
            </div>
            <div className="grid grid-cols-7 gap-1 text-center">
              {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(day => (
                <div key={day} className="text-sm font-medium text-gray-500 py-2">{day}</div>
              ))}
              {[...Array(30)].map((_, i) => {
                // Simple calendar logic
                const day = i + 1;
                const isToday = day === 17;
                const isWeekend = i % 7 === 0 || i % 7 === 6;
                const isPast = day < 17;
                
                return (
                  <div 
                    key={i} 
                    className={`
                      rounded-lg text-sm p-1
                      ${isToday ? 'bg-blue-600 text-white' : isWeekend ? 'bg-gray-100 text-gray-400' : isPast ? 'bg-green-50 text-gray-700' : 'bg-white text-gray-700'}
                      ${!isWeekend && !isToday ? 'border border-gray-200' : ''}
                      ${isPast && !isWeekend ? 'border-green-200' : ''}
                    `}
                  >
                    <div className="p-1">{day}</div>
                    {!isWeekend && day <= 17 && (
                      <div className={`text-xs mt-1 ${isToday ? 'text-blue-200' : 'text-gray-500'}`}>
                        {Math.floor(Math.random() * 4 + 6)}h
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </main>
      </div>
    </div>
  );
};

// Helper components
const NavItem = ({ icon, label, active, collapsed, onClick }) => (
  <button
    onClick={onClick}
    className={`
      w-full flex items-center py-3 px-4 
      ${active ? 'bg-blue-700 text-white' : 'text-gray-300 hover:bg-slate-700'}
      ${collapsed ? 'justify-center' : 'justify-start'}
      transition-colors
    `}
  >
    <span className="flex-shrink-0">{icon}</span>
    {!collapsed && <span className="ml-3">{label}</span>}
  </button>
);

const SummaryCard = ({ title, value, subvalue, progress, detail, colorClass = 'bg-blue-600' }) => (
  <div className="bg-white rounded-xl shadow-sm p-6">
    <h3 className="text-sm font-medium text-gray-500 mb-1">{title}</h3>
    <div className="flex items-baseline">
      <span className="text-2xl font-bold text-gray-800">{value}</span>
      <span className="ml-1 text-gray-500">{subvalue}</span>
    </div>
    {progress !== undefined && (
      <div className="mt-3">
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div 
            className={`${colorClass} rounded-full h-2`} 
            style={{ width: `${progress}%` }}
          ></div>
        </div>
      </div>
    )}
    <p className="mt-2 text-sm text-gray-600">{detail}</p>
  </div>
);

export default DashboardRedesign;
