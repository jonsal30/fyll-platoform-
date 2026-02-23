import { useState, useEffect, useRef, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { toast } from "sonner";
import { useAuth, API } from "../App";
import Layout from "../components/Layout";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { Badge } from "../components/ui/badge";
import { 
  Clock, MapPin, Camera, Coffee, LogOut, CheckCircle2, 
  AlertCircle, Navigation, Loader2 
} from "lucide-react";

const Dashboard = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);

  const [clockStatus, setClockStatus] = useState(null);
  const [sites, setSites] = useState([]);
  const [selectedSite, setSelectedSite] = useState("");
  const [location, setLocation] = useState(null);
  const [locationError, setLocationError] = useState(null);
  const [loading, setLoading] = useState(true);
  const [clockLoading, setClockLoading] = useState(false);
  const [cameraActive, setCameraActive] = useState(false);
  const [capturedPhoto, setCapturedPhoto] = useState(null);
  const [elapsedTime, setElapsedTime] = useState(0);
  const [isOnLunch, setIsOnLunch] = useState(false);

  // Fetch initial data
  useEffect(() => {
    const fetchData = async () => {
      try {
        const [statusRes, sitesRes] = await Promise.all([
          axios.get(`${API}/clock/status`),
          axios.get(`${API}/sites`)
        ]);
        
        setClockStatus(statusRes.data);
        setSites(sitesRes.data);
        
        if (statusRes.data.is_clocked_in && statusRes.data.entry) {
          setSelectedSite(statusRes.data.entry.site_id);
          const entry = statusRes.data.entry;
          setIsOnLunch(entry.lunch_start && !entry.lunch_end);
        } else if (sitesRes.data.length > 0) {
          setSelectedSite(sitesRes.data[0].site_id);
        }
      } catch (error) {
        toast.error("Failed to load data");
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  // Get location
  useEffect(() => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setLocation({
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
            accuracy: position.coords.accuracy
          });
          setLocationError(null);
        },
        (error) => {
          setLocationError("Unable to get location. Please enable GPS.");
        },
        { enableHighAccuracy: true, timeout: 10000 }
      );
    } else {
      setLocationError("Geolocation not supported");
    }
  }, []);

  // Timer for elapsed time
  useEffect(() => {
    if (!clockStatus?.is_clocked_in || !clockStatus?.entry?.clock_in) return;

    const clockIn = new Date(clockStatus.entry.clock_in);
    
    const updateElapsed = () => {
      const now = new Date();
      let elapsed = Math.floor((now - clockIn) / 1000);
      
      // Subtract lunch time if on lunch or lunch completed
      if (clockStatus.entry.lunch_start) {
        const lunchStart = new Date(clockStatus.entry.lunch_start);
        if (clockStatus.entry.lunch_end) {
          const lunchEnd = new Date(clockStatus.entry.lunch_end);
          elapsed -= Math.floor((lunchEnd - lunchStart) / 1000);
        } else {
          elapsed -= Math.floor((now - lunchStart) / 1000);
        }
      }
      
      setElapsedTime(Math.max(0, elapsed));
    };

    updateElapsed();
    const interval = setInterval(updateElapsed, 1000);
    return () => clearInterval(interval);
  }, [clockStatus]);

  // Format elapsed time
  const formatTime = (seconds) => {
    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    return `${hrs.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  // Camera functions
  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        video: { facingMode: "user", width: 640, height: 480 } 
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
      setCameraActive(true);
      setCapturedPhoto(null);
    } catch (error) {
      toast.error("Unable to access camera");
    }
  };

  const capturePhoto = () => {
    if (!videoRef.current || !canvasRef.current) return;
    
    const canvas = canvasRef.current;
    const video = videoRef.current;
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    
    const ctx = canvas.getContext("2d");
    ctx.drawImage(video, 0, 0);
    
    const photoData = canvas.toDataURL("image/jpeg", 0.7);
    setCapturedPhoto(photoData);
    
    // Stop camera after capture
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
    }
    setCameraActive(false);
  };

  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
    }
    setCameraActive(false);
  };

  // Clock actions
  const handleClockIn = async () => {
    if (!selectedSite) {
      toast.error("Please select a work site");
      return;
    }
    if (!location) {
      toast.error("Location required for clock-in");
      return;
    }

    setClockLoading(true);
    try {
      const response = await axios.post(`${API}/clock/in`, {
        site_id: selectedSite,
        photo: capturedPhoto,
        latitude: location.latitude,
        longitude: location.longitude
      });

      setClockStatus({ is_clocked_in: true, entry: response.data, site: sites.find(s => s.site_id === selectedSite) });
      setCapturedPhoto(null);
      
      if (response.data.location_verified) {
        toast.success("Clocked in successfully! Location verified.");
      } else {
        toast.warning(`Clocked in, but you're ${Math.round(response.data.distance_from_site)}m from site.`);
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to clock in");
    } finally {
      setClockLoading(false);
    }
  };

  const handleClockOut = async () => {
    if (!clockStatus?.entry?.entry_id) return;
    if (!location) {
      toast.error("Location required for clock-out");
      return;
    }

    setClockLoading(true);
    try {
      const response = await axios.post(`${API}/clock/out`, {
        entry_id: clockStatus.entry.entry_id,
        photo: capturedPhoto,
        latitude: location.latitude,
        longitude: location.longitude
      });

      toast.success(`Clocked out! Total hours: ${response.data.total_hours}`);
      setClockStatus({ is_clocked_in: false, entry: null, site: null });
      setCapturedPhoto(null);
      setElapsedTime(0);
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to clock out");
    } finally {
      setClockLoading(false);
    }
  };

  const handleLunch = async (action) => {
    if (!clockStatus?.entry?.entry_id) return;

    try {
      await axios.post(`${API}/clock/lunch`, {
        entry_id: clockStatus.entry.entry_id,
        action
      });

      const statusRes = await axios.get(`${API}/clock/status`);
      setClockStatus(statusRes.data);
      setIsOnLunch(action === "start");
      
      toast.success(action === "start" ? "Lunch started" : "Lunch ended");
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to update lunch status");
    }
  };

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-96">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
        </div>
      </Layout>
    );
  }

  const currentSite = sites.find(s => s.site_id === selectedSite);

  return (
    <Layout>
      <div className="max-w-md mx-auto space-y-6 p-4">
        {/* Status Header */}
        <div className="text-center">
          <h1 className="font-heading text-3xl font-bold">
            {clockStatus?.is_clocked_in ? "ON DUTY" : "OFF DUTY"}
          </h1>
          <p className="text-muted-foreground">
            Welcome, {user?.name?.split(" ")[0]}
          </p>
        </div>

        {/* Time Display */}
        {clockStatus?.is_clocked_in && (
          <Card className="bg-card border-border">
            <CardContent className="p-6 text-center">
              <p className="text-muted-foreground text-sm mb-2">
                {isOnLunch ? "ON LUNCH BREAK" : "TIME WORKED"}
              </p>
              <p className="font-mono text-5xl font-bold text-foreground">
                {formatTime(elapsedTime)}
              </p>
              <div className="flex items-center justify-center gap-2 mt-3">
                <Badge variant={clockStatus.entry?.location_verified ? "default" : "destructive"} className="flex items-center gap-1">
                  {clockStatus.entry?.location_verified ? (
                    <><CheckCircle2 className="w-3 h-3" /> Location Verified</>
                  ) : (
                    <><AlertCircle className="w-3 h-3" /> Off-site</>
                  )}
                </Badge>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Site Selection (only when not clocked in) */}
        {!clockStatus?.is_clocked_in && (
          <Card className="bg-card border-border">
            <CardHeader className="pb-3">
              <CardTitle className="font-heading text-lg flex items-center gap-2">
                <MapPin className="w-5 h-5 text-primary" />
                Select Work Site
              </CardTitle>
            </CardHeader>
            <CardContent>
              <Select value={selectedSite} onValueChange={setSelectedSite}>
                <SelectTrigger data-testid="site-select" className="h-12 bg-background">
                  <SelectValue placeholder="Choose a site" />
                </SelectTrigger>
                <SelectContent>
                  {sites.map((site) => (
                    <SelectItem key={site.site_id} value={site.site_id}>
                      {site.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {currentSite && (
                <p className="text-xs text-muted-foreground mt-2">
                  {currentSite.address} • {currentSite.radius_meters}m radius
                </p>
              )}
            </CardContent>
          </Card>
        )}

        {/* Location Status */}
        <Card className="bg-card border-border">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Navigation className="w-5 h-5 text-secondary" />
                <span className="text-sm">GPS Location</span>
              </div>
              {location ? (
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-success glow-success"></div>
                  <span className="text-xs text-muted-foreground font-mono">
                    ±{Math.round(location.accuracy)}m
                  </span>
                </div>
              ) : (
                <div className="flex items-center gap-2 text-destructive">
                  <AlertCircle className="w-4 h-4" />
                  <span className="text-xs">{locationError || "Acquiring..."}</span>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Camera Section */}
        <Card className="bg-card border-border">
          <CardHeader className="pb-3">
            <CardTitle className="font-heading text-lg flex items-center gap-2">
              <Camera className="w-5 h-5 text-primary" />
              Photo Verification
            </CardTitle>
          </CardHeader>
          <CardContent>
            {cameraActive ? (
              <div className="space-y-3">
                <video
                  ref={videoRef}
                  autoPlay
                  playsInline
                  muted
                  className="w-full rounded-sm bg-black aspect-video"
                />
                <div className="flex gap-2">
                  <Button onClick={capturePhoto} className="flex-1 bg-primary">
                    Capture
                  </Button>
                  <Button onClick={stopCamera} variant="outline" className="flex-1">
                    Cancel
                  </Button>
                </div>
              </div>
            ) : capturedPhoto ? (
              <div className="space-y-3">
                <img src={capturedPhoto} alt="Captured" className="w-full rounded-sm" />
                <div className="flex gap-2">
                  <Button onClick={() => setCapturedPhoto(null)} variant="outline" className="flex-1">
                    Retake
                  </Button>
                  <div className="flex-1 flex items-center justify-center text-success">
                    <CheckCircle2 className="w-5 h-5 mr-2" />
                    Ready
                  </div>
                </div>
              </div>
            ) : (
              <Button 
                data-testid="start-camera-btn"
                onClick={startCamera} 
                variant="outline" 
                className="w-full h-24 border-dashed flex flex-col gap-2"
              >
                <Camera className="w-8 h-8" />
                <span>Tap to take photo</span>
              </Button>
            )}
            <canvas ref={canvasRef} className="hidden" />
          </CardContent>
        </Card>

        {/* Main Clock Button */}
        <div className="flex flex-col items-center py-4">
          {clockStatus?.is_clocked_in ? (
            <>
              {/* Lunch Button */}
              {!isOnLunch && !clockStatus.entry?.lunch_end && (
                <Button
                  data-testid="lunch-start-btn"
                  onClick={() => handleLunch("start")}
                  variant="outline"
                  className="w-full mb-4 h-12 flex items-center gap-2"
                >
                  <Coffee className="w-5 h-5" />
                  Start Lunch Break
                </Button>
              )}
              {isOnLunch && (
                <Button
                  data-testid="lunch-end-btn"
                  onClick={() => handleLunch("end")}
                  className="w-full mb-4 h-12 bg-secondary flex items-center gap-2"
                >
                  <Coffee className="w-5 h-5" />
                  End Lunch Break
                </Button>
              )}

              {/* Clock Out Button */}
              <button
                data-testid="clock-out-btn"
                onClick={handleClockOut}
                disabled={clockLoading || isOnLunch}
                className="clock-button w-40 h-40 rounded-full border-4 border-muted bg-card flex flex-col items-center justify-center text-destructive hover:border-destructive transition-all disabled:opacity-50"
              >
                {clockLoading ? (
                  <Loader2 className="w-8 h-8 animate-spin" />
                ) : (
                  <>
                    <LogOut className="w-10 h-10 mb-2" />
                    <span className="font-heading text-xl font-bold">CLOCK OUT</span>
                  </>
                )}
              </button>
            </>
          ) : (
            <button
              data-testid="clock-in-btn"
              onClick={handleClockIn}
              disabled={clockLoading || !location || !selectedSite}
              className="clock-button w-44 h-44 rounded-full border-4 border-primary bg-card flex flex-col items-center justify-center text-primary hover:glow-primary transition-all disabled:opacity-50 disabled:border-muted"
            >
              {clockLoading ? (
                <Loader2 className="w-8 h-8 animate-spin" />
              ) : (
                <>
                  <Clock className="w-12 h-12 mb-2" />
                  <span className="font-heading text-2xl font-bold">CLOCK IN</span>
                </>
              )}
            </button>
          )}

          {!location && !clockStatus?.is_clocked_in && (
            <p className="text-xs text-destructive mt-4">
              Waiting for GPS location...
            </p>
          )}
        </div>

        {/* Current Site Info */}
        {clockStatus?.is_clocked_in && clockStatus.site && (
          <Card className="bg-card border-t-2 border-t-primary border-border">
            <CardContent className="p-4">
              <div className="flex items-start justify-between">
                <div>
                  <p className="font-heading text-lg font-semibold">{clockStatus.site.name}</p>
                  <p className="text-xs text-muted-foreground">{clockStatus.site.address}</p>
                </div>
                <Badge variant="secondary" className="font-mono text-xs">
                  {clockStatus.site.radius_meters}m
                </Badge>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </Layout>
  );
};

export default Dashboard;
