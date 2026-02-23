import { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { toast } from "sonner";
import { useAuth, API } from "../App";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import { User, KeyRound } from "lucide-react";

const Login = () => {
  const navigate = useNavigate();
  const { user, login } = useAuth();
  const [numericId, setNumericId] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (user) {
      navigate("/dashboard", { replace: true });
    }
  }, [user, navigate]);

  const handleNumericLogin = async (e) => {
    e.preventDefault();
    if (!numericId.trim()) {
      toast.error("Please enter your Employee ID");
      return;
    }
    
    setLoading(true);
    try {
      const response = await axios.post(`${API}/auth/numeric-login`, {
        numeric_id: numericId
      });
      login(response.data);
      toast.success("Welcome back!");
      navigate("/dashboard", { replace: true });
    } catch (error) {
      toast.error(error.response?.data?.detail || "Invalid Employee ID");
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleLogin = () => {
    // REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
    const redirectUrl = window.location.origin + '/dashboard';
    window.location.href = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirectUrl)}`;
  };

  return (
    <div 
      className="min-h-screen flex items-center justify-center p-4 relative"
      style={{
        backgroundImage: `linear-gradient(to bottom, rgba(9,9,11,0.85), rgba(9,9,11,0.95)), url(https://images.pexels.com/photos/12418936/pexels-photo-12418936.jpeg)`,
        backgroundSize: 'cover',
        backgroundPosition: 'center'
      }}
    >
      <div className="w-full max-w-md space-y-6">
        {/* Logo/Title */}
        <div className="text-center mb-8">
          <h1 className="font-heading text-5xl font-bold text-foreground tracking-tight">
            SITE COMMANDER
          </h1>
          <p className="text-muted-foreground mt-2">Workforce Time Tracking</p>
        </div>

        <Card className="bg-card/80 backdrop-blur-sm border-border">
          <CardHeader className="space-y-1 pb-4">
            <CardTitle className="font-heading text-2xl text-center">Sign In</CardTitle>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue="numeric" className="w-full">
              <TabsList className="grid w-full grid-cols-2 mb-6">
                <TabsTrigger value="numeric" data-testid="numeric-tab" className="flex items-center gap-2">
                  <KeyRound className="w-4 h-4" />
                  Employee ID
                </TabsTrigger>
                <TabsTrigger value="google" data-testid="google-tab" className="flex items-center gap-2">
                  <User className="w-4 h-4" />
                  Google
                </TabsTrigger>
              </TabsList>

              <TabsContent value="numeric">
                <form onSubmit={handleNumericLogin} className="space-y-4">
                  <div className="space-y-2">
                    <label className="text-sm text-muted-foreground">Employee ID</label>
                    <Input
                      data-testid="numeric-id-input"
                      type="text"
                      placeholder="Enter your employee ID"
                      value={numericId}
                      onChange={(e) => setNumericId(e.target.value)}
                      className="h-12 text-lg font-mono bg-background border-border focus:border-primary"
                    />
                  </div>
                  <Button
                    data-testid="numeric-login-btn"
                    type="submit"
                    disabled={loading}
                    className="w-full h-12 bg-primary text-primary-foreground font-bold tracking-wide uppercase hover:bg-primary/90 glow-primary"
                  >
                    {loading ? "Signing in..." : "Clock In"}
                  </Button>
                </form>
              </TabsContent>

              <TabsContent value="google">
                <div className="space-y-4">
                  <p className="text-sm text-muted-foreground text-center">
                    Sign in with your company Google account
                  </p>
                  <Button
                    data-testid="google-login-btn"
                    type="button"
                    onClick={handleGoogleLogin}
                    className="w-full h-12 bg-card border border-border hover:bg-muted font-medium flex items-center justify-center gap-3"
                  >
                    <svg className="w-5 h-5" viewBox="0 0 24 24">
                      <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                      <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                      <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                      <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                    </svg>
                    Continue with Google
                  </Button>
                </div>
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>

        <p className="text-center text-xs text-muted-foreground">
          By signing in, you agree to the company time tracking policy
        </p>
      </div>
    </div>
  );
};

export default Login;
