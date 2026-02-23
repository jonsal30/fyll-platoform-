import { useState, useEffect } from "react";
import { NavLink, useNavigate, useLocation } from "react-router-dom";
import axios from "axios";
import { useAuth, API } from "../App";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { 
  Clock, FileText, Users, Settings, LogOut, Menu, X, 
  Bell, Home, ChevronRight
} from "lucide-react";

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
    { to: "/dashboard", icon: Home, label: "Dashboard" },
    { to: "/timesheet", icon: FileText, label: "Timesheet" },
    ...(user?.role === "manager" || user?.role === "admin" 
      ? [{ to: "/manager", icon: Users, label: "Manager" }] 
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
        flex items-center gap-3 px-4 py-3 rounded-sm transition-all
        ${isActive 
          ? "bg-primary/10 text-primary border-l-2 border-primary" 
          : "text-muted-foreground hover:bg-muted hover:text-foreground"
        }
        ${mobile ? "text-lg" : "text-sm"}
      `}
    >
      <item.icon className="w-5 h-5" />
      <span className="font-medium">{item.label}</span>
    </NavLink>
  );

  return (
    <div className="min-h-screen flex flex-col lg:flex-row">
      {/* Desktop Sidebar */}
      <aside className="hidden lg:flex lg:flex-col lg:w-64 bg-card border-r border-border">
        {/* Logo */}
        <div className="p-6 border-b border-border">
          <h1 className="font-heading text-2xl font-bold tracking-tight">
            SITE COMMANDER
          </h1>
          <p className="text-xs text-muted-foreground mt-1">Time Tracking</p>
        </div>

        {/* User Info */}
        <div className="p-4 border-b border-border">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-muted flex items-center justify-center overflow-hidden">
              {user?.picture ? (
                <img src={user.picture} alt="" className="w-full h-full object-cover" />
              ) : (
                <Users className="w-5 h-5 text-muted-foreground" />
              )}
            </div>
            <div className="flex-1 min-w-0">
              <p className="font-medium text-sm truncate">{user?.name}</p>
              <Badge variant="outline" className="text-xs mt-0.5">
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

        {/* Logout */}
        <div className="p-4 border-t border-border">
          <Button
            variant="ghost"
            onClick={handleLogout}
            className="w-full justify-start text-muted-foreground hover:text-destructive"
            data-testid="logout-btn"
          >
            <LogOut className="w-5 h-5 mr-3" />
            Sign Out
          </Button>
        </div>
      </aside>

      {/* Mobile Header */}
      <header className="lg:hidden sticky top-0 z-50 bg-card/80 backdrop-blur-sm border-b border-border">
        <div className="flex items-center justify-between p-4">
          <h1 className="font-heading text-xl font-bold">SITE COMMANDER</h1>
          
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="icon" className="relative" data-testid="notifications-btn">
              <Bell className="w-5 h-5" />
              {unreadCount > 0 && (
                <span className="absolute -top-1 -right-1 w-5 h-5 bg-primary text-primary-foreground text-xs rounded-full flex items-center justify-center">
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
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </Button>
          </div>
        </div>

        {/* Mobile Menu */}
        {mobileMenuOpen && (
          <div className="absolute inset-x-0 top-full bg-card border-b border-border shadow-lg">
            <div className="p-4 border-b border-border">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-muted flex items-center justify-center overflow-hidden">
                  {user?.picture ? (
                    <img src={user.picture} alt="" className="w-full h-full object-cover" />
                  ) : (
                    <Users className="w-5 h-5 text-muted-foreground" />
                  )}
                </div>
                <div>
                  <p className="font-medium">{user?.name}</p>
                  <Badge variant="outline" className="text-xs">{user?.role}</Badge>
                </div>
              </div>
            </div>
            
            <nav className="p-4 space-y-1">
              {navItems.map((item) => (
                <NavItem key={item.to} item={item} mobile />
              ))}
            </nav>
            
            <div className="p-4 border-t border-border">
              <Button
                variant="ghost"
                onClick={handleLogout}
                className="w-full justify-start text-destructive"
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
      <nav className="lg:hidden fixed bottom-0 left-0 right-0 bg-card/95 backdrop-blur-sm border-t border-border safe-area-bottom z-40">
        <div className="flex justify-around items-center py-2">
          {navItems.slice(0, 4).map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) => `
                flex flex-col items-center gap-1 px-3 py-2 min-w-[64px]
                ${isActive ? "text-primary" : "text-muted-foreground"}
              `}
            >
              <item.icon className="w-5 h-5" />
              <span className="text-xs">{item.label}</span>
            </NavLink>
          ))}
        </div>
      </nav>
    </div>
  );
};

export default Layout;
