import { useState, useEffect } from "react";
import { NavLink, useNavigate, useLocation } from "react-router-dom";
import axios from "axios";
import { useAuth, API } from "../App";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { 
  Clock, FileText, Users, Settings, LogOut, Menu, X, 
  Bell, Home, ChevronRight, Briefcase, Building2, BarChart3
} from "lucide-react";

const Brand = ({ compact = false }) => (
  <div className="flex items-center gap-2" aria-label="GH Service Group">
    <div className={`${compact ? "w-8 h-8 text-xs" : "w-10 h-10 text-sm"} rounded-lg bg-keystone text-white flex items-center justify-center font-black`}>GH</div>
    <div className="leading-tight">
      <div className={`${compact ? "text-sm" : "text-base"} font-serif font-bold text-foundation`}>GH Service Group</div>
      {!compact && <div className="text-[10px] uppercase tracking-widest text-foundation/50">Workforce Portal</div>}
    </div>
  </div>
);

const Layout = ({ children }) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);

  useEffect(() => {
    const fetchNotifications = async () => {
      try {
        const response = await axios.get(`${API}/notifications/unread-count`);
        setUnreadCount(response.data.count);
      } catch (error) {
        // Ignore errors
      }
    };
    
    fetchNotifications();
    const interval = setInterval(fetchNotifications, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleLogout = async () => {
    await logout();
    navigate("/login", { replace: true });
  };

  const navItems = [
    { to: "/dashboard", icon: Home, label: "Clock" },
    { to: "/timesheet", icon: FileText, label: "Timesheet" },
    ...(user?.role === "manager" || user?.role === "admin" 
      ? [
          { to: "/manager", icon: Users, label: "Approvals" },
          { to: "/recruiting", icon: Briefcase, label: "Recruiting" }
        ] 
      : []),
    ...(user?.role === "admin" 
      ? [{ to: "/admin", icon: Settings, label: "Admin" }] 
      : [])
  ];

  const NavItem = ({ item, mobile = false }) => (
    <NavLink
      to={item.to}
      onClick={() => mobile && setMobileMenuOpen(false)}
      className={({ isActive }) => `
        flex items-center gap-3 px-4 py-3 rounded transition-all
        ${isActive 
          ? "bg-keystone text-white" 
          : "text-foundation/70 hover:bg-horizon hover:text-foundation"
        }
        ${mobile ? "text-lg" : "text-sm"}
      `}
    >
      <item.icon className="w-5 h-5" />
      <span className="font-medium">{item.label}</span>
    </NavLink>
  );

  return (
    <div className="min-h-screen flex flex-col lg:flex-row bg-horizon">
      {/* Desktop Sidebar */}
      <aside className="hidden lg:flex lg:flex-col lg:w-64 bg-white border-r border-gray-200 shadow-sm">
        {/* Logo */}
        <div className="p-4 border-b border-gray-100">
          <Brand />
        </div>

        {/* User Info */}
        <div className="p-4 border-b border-gray-100">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-keystone/10 flex items-center justify-center overflow-hidden">
              {user?.picture ? (
                <img src={user.picture} alt="" className="w-full h-full object-cover" />
              ) : (
                <Users className="w-5 h-5 text-keystone" />
              )}
            </div>
            <div className="flex-1 min-w-0">
              <p className="font-medium text-sm text-foundation truncate">{user?.name}</p>
              <Badge 
                variant="outline" 
                className="text-xs mt-0.5 border-keystone/30 text-keystone"
              >
                {user?.role}
              </Badge>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-1">
          {navItems.map((item) => (
            <NavItem key={item.to} item={item} />
          ))}
        </nav>

        {/* Tagline */}
        <div className="px-4 py-3 border-t border-gray-100">
          <p className="text-xs text-muted-foreground italic font-serif text-center">
            "Service driven. People supported."
          </p>
        </div>

        {/* Logout */}
        <div className="p-4 border-t border-gray-100">
          <Button
            variant="ghost"
            onClick={handleLogout}
            className="w-full justify-start text-foundation/60 hover:text-vertex hover:bg-vertex/5"
            data-testid="logout-btn"
          >
            <LogOut className="w-5 h-5 mr-3" />
            Sign Out
          </Button>
        </div>
      </aside>

      {/* Mobile Header */}
      <header className="lg:hidden sticky top-0 z-50 bg-white border-b border-gray-200 shadow-sm">
        <div className="flex items-center justify-between p-3">
          <Brand compact />
          
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="icon" className="relative" data-testid="notifications-btn">
              <Bell className="w-5 h-5 text-foundation" />
              {unreadCount > 0 && (
                <span className="absolute -top-1 -right-1 w-5 h-5 bg-vertex text-white text-xs rounded-full flex items-center justify-center">
                  {unreadCount > 9 ? "9+" : unreadCount}
                </span>
              )}
            </Button>
            <Button 
              variant="ghost" 
              size="icon" 
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              data-testid="mobile-menu-btn"
            >
              {mobileMenuOpen ? <X className="w-6 h-6 text-foundation" /> : <Menu className="w-6 h-6 text-foundation" />}
            </Button>
          </div>
        </div>

        {/* Mobile Menu */}
        {mobileMenuOpen && (
          <div className="absolute inset-x-0 top-full bg-white border-b border-gray-200 shadow-lg">
            <div className="p-4 border-b border-gray-100 bg-horizon/50">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-keystone/10 flex items-center justify-center overflow-hidden">
                  {user?.picture ? (
                    <img src={user.picture} alt="" className="w-full h-full object-cover" />
                  ) : (
                    <Users className="w-5 h-5 text-keystone" />
                  )}
                </div>
                <div>
                  <p className="font-medium text-foundation">{user?.name}</p>
                  <Badge variant="outline" className="text-xs border-keystone/30 text-keystone">
                    {user?.role}
                  </Badge>
                </div>
              </div>
            </div>
            
            <nav className="p-4 space-y-1">
              {navItems.map((item) => (
                <NavItem key={item.to} item={item} mobile />
              ))}
            </nav>
            
            <div className="p-4 border-t border-gray-100">
              <Button
                variant="ghost"
                onClick={handleLogout}
                className="w-full justify-start text-vertex"
              >
                <LogOut className="w-5 h-5 mr-3" />
                Sign Out
              </Button>
            </div>
          </div>
        )}
      </header>

      {/* Main Content */}
      <main className="flex-1 overflow-auto">
        {children}
      </main>

      {/* Mobile Bottom Nav */}
      <nav className="lg:hidden fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 safe-area-bottom z-40">
        <div className="flex justify-around items-center py-2">
          {navItems.slice(0, 4).map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) => `
                flex flex-col items-center gap-1 px-3 py-2 min-w-[64px]
                ${isActive ? "text-keystone" : "text-foundation/50"}
              `}
            >
              <item.icon className="w-5 h-5" />
              <span className="text-xs font-medium">{item.label}</span>
            </NavLink>
          ))}
        </div>
      </nav>
    </div>
  );
};

export default Layout;
