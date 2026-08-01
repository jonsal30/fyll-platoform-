import { useState, useEffect, useRef } from "react";
import axios from "axios";
import { toast } from "sonner";
import { useAuth, API } from "../App";
import Layout from "../components/Layout";
import { Button } from "../components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "../components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";
import { Badge } from "../components/ui/badge";
import {
  Bus,
  Clock,
  MapPin,
  Camera,
  Coffee,
  LogOut,
  CheckCircle2,
  AlertCircle,
  Navigation,
  Loader2,
  BriefcaseBusiness,
  RotateCcw,
} from "lucide-react";

const ACTIONS = {
  shuttle_check_in: {
    label: "Check In for Shuttle",
    detail: "Attendance only — paid time has not started.",
    icon: Bus,
    color: "keystone",
  },
  work_start: {
    label: "Start Work",
    detail: "Begins your paid work time.",
    icon: BriefcaseBusiness,
    color: "keystone",
  },
  lunch_out: {
    label: "Start Lunch",
    detail: "Pauses paid work time for lunch.",
    icon: Coffee,
    color: "foundation",
  },
  lunch_in: {
    label: "Return from Lunch",
    detail: "Resumes paid work time.",
    icon: RotateCcw,
    color: "keystone",
  },
  work_end: {
    label: "End Work",
    detail: "Ends your paid work time.",
    icon: LogOut,
    color: "vertex",
  },
  browne_check_out: {
    label: "Check Out at Browne",
    detail: "Confirms return to the Browne lot. Attendance only.",
    icon: MapPin,
    color: "foundation",
  },
};

const formatElapsed = (seconds) => {
  const hrs = Math.floor(seconds / 3600);
  const mins = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;
  return [hrs, mins, secs]
    .map((value) => value.toString().padStart(2, "0"))
    .join(":");
};

const Dashboard = () => {
  const { user } = useAuth();
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);

  const [clockStatus, setClockStatus] = useState(null);
  const [attendance, setAttendance] = useState(null);
  const [sites, setSites] = useState([]);
  const [selectedSite, setSelectedSite] = useState("");
  const [location, setLocation] = useState(null);
  const [locationError, setLocationError] = useState(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [cameraActive, setCameraActive] = useState(false);
  const [capturedPhoto, setCapturedPhoto] = useState(null);
  const [elapsedTime, setElapsedTime] = useState(0);

  const refresh = async () => {
    const [clockRes, attendanceRes, sitesRes] = await Promise.all([
      axios.get(`${API}/clock/status`),
      axios.get(`${API}/attendance/status`),
      axios.get(`${API}/sites`),
    ]);
    setClockStatus(clockRes.data);
    setAttendance(attendanceRes.data);
    setSites(sitesRes.data);
    const activeSite =
      clockRes.data.entry?.site_id || attendanceRes.data.session?.site_id;
    setSelectedSite(activeSite || sitesRes.data[0]?.site_id || "");
  };

  useEffect(() => {
    refresh()
      .catch(() => toast.error("Failed to load attendance data"))
      .finally(() => setLoading(false));
  }, []);

  const acquireLocation = () =>
    new Promise((resolve, reject) => {
      if (!navigator.geolocation) {
        reject(new Error("Geolocation is not supported on this device."));
        return;
      }
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const next = {
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
            accuracy: position.coords.accuracy,
          };
          setLocation(next);
          setLocationError(null);
          resolve(next);
        },
        () => {
          const message =
            "Unable to get location. Enable Precise Location for this browser.";
          setLocationError(message);
          reject(new Error(message));
        },
        { enableHighAccuracy: true, timeout: 15000, maximumAge: 0 },
      );
    });

  useEffect(() => {
    acquireLocation().catch(() => {});
  }, []);

  useEffect(() => {
    const clockIn = clockStatus?.entry?.clock_in;
    if (!clockStatus?.is_clocked_in || !clockIn) {
      setElapsedTime(0);
      return;
    }
    const update = () => {
      const now = new Date();
      let seconds = Math.floor((now - new Date(clockIn)) / 1000);
      if (clockStatus.entry.lunch_start) {
        const lunchStart = new Date(clockStatus.entry.lunch_start);
        const lunchEnd = clockStatus.entry.lunch_end
          ? new Date(clockStatus.entry.lunch_end)
          : now;
        seconds -= Math.floor((lunchEnd - lunchStart) / 1000);
      }
      setElapsedTime(Math.max(0, seconds));
    };
    update();
    const interval = setInterval(update, 1000);
    return () => clearInterval(interval);
  }, [clockStatus]);

  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "user", width: 640, height: 480 },
      });
      streamRef.current = stream;
      if (videoRef.current) videoRef.current.srcObject = stream;
      setCameraActive(true);
      setCapturedPhoto(null);
    } catch {
      toast.error("Unable to access camera");
    }
  };

  const stopCamera = () => {
    streamRef.current?.getTracks().forEach((track) => track.stop());
    setCameraActive(false);
  };

  const capturePhoto = () => {
    if (!videoRef.current || !canvasRef.current) return;
    const canvas = canvasRef.current;
    canvas.width = videoRef.current.videoWidth;
    canvas.height = videoRef.current.videoHeight;
    canvas.getContext("2d").drawImage(videoRef.current, 0, 0);
    setCapturedPhoto(canvas.toDataURL("image/jpeg", 0.7));
    stopCamera();
  };

  const recordAttendance = (eventType, currentLocation) =>
    axios.post(`${API}/attendance/event`, {
      event_type: eventType,
      site_id: selectedSite || null,
      ...currentLocation,
    });

  const handleAction = async () => {
    const eventType = attendance?.next_event;
    if (!eventType) return;
    if (
      ["shuttle_check_in", "work_start"].includes(eventType) &&
      !selectedSite
    ) {
      toast.error("Select your assigned work site");
      return;
    }
    if (["work_start", "work_end"].includes(eventType) && !capturedPhoto) {
      toast.error("Take a verification photo first");
      return;
    }

    setActionLoading(true);
    try {
      const currentLocation = await acquireLocation();

      if (eventType === "shuttle_check_in") {
        await recordAttendance(eventType, currentLocation);
      } else if (eventType === "work_start") {
        const clockRes = await axios.post(`${API}/clock/in`, {
          site_id: selectedSite,
          photo: capturedPhoto,
          latitude: currentLocation.latitude,
          longitude: currentLocation.longitude,
        });
        try {
          await recordAttendance(eventType, currentLocation);
        } catch (error) {
          await axios.post(`${API}/clock/out`, {
            entry_id: clockRes.data.entry_id,
            photo: null,
            latitude: currentLocation.latitude,
            longitude: currentLocation.longitude,
          });
          throw error;
        }
      } else if (eventType === "lunch_out" || eventType === "lunch_in") {
        const action = eventType === "lunch_out" ? "start" : "end";
        await axios.post(`${API}/clock/lunch`, {
          entry_id: clockStatus.entry.entry_id,
          action,
        });
        await recordAttendance(eventType, currentLocation);
      } else if (eventType === "work_end") {
        await axios.post(`${API}/clock/out`, {
          entry_id: clockStatus.entry.entry_id,
          photo: capturedPhoto,
          latitude: currentLocation.latitude,
          longitude: currentLocation.longitude,
        });
        await recordAttendance(eventType, currentLocation);
      } else {
        await recordAttendance(eventType, currentLocation);
      }

      setCapturedPhoto(null);
      await refresh();
      toast.success(`${ACTIONS[eventType].label} recorded`);
    } catch (error) {
      toast.error(
        error.response?.data?.detail ||
          error.message ||
          "Unable to record this action",
      );
      await refresh().catch(() => {});
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-96">
          <Loader2 className="w-8 h-8 animate-spin text-keystone" />
        </div>
      </Layout>
    );
  }

  const nextEvent = attendance?.next_event;
  const action = ACTIONS[nextEvent];
  const ActionIcon = action?.icon || Clock;
  const currentSite = sites.find((site) => site.site_id === selectedSite);
  const trainingDay =
    attendance?.session?.training_day ||
    Math.min((attendance?.completed_days || 0) + 1, 5);
  const needsPhoto = ["work_start", "work_end"].includes(nextEvent);
  const isOnLunch = nextEvent === "lunch_in";

  return (
    <Layout>
      <div className="max-w-md mx-auto space-y-5 p-4 pb-28 lg:pb-6">
        <header>
          <p className="text-sm text-muted-foreground">
            Welcome, {user?.name?.split(" ")[0]}
          </p>
          <h1 className="font-serif text-3xl font-bold text-foundation">
            Brownsville Attendance
          </h1>
        </header>

        {attendance?.location_capture_required && (
          <div className="rounded-xl border border-keystone/20 bg-keystone/5 p-3 flex gap-3">
            <Navigation className="w-5 h-5 text-keystone shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-semibold text-foundation">
                Location setup · Day {trainingDay} of 5
              </p>
              <p className="text-xs text-muted-foreground">
                Today’s punch locations help GHSG confirm future geofence
                boundaries.
              </p>
            </div>
          </div>
        )}

        <Card className="bg-white border-0 shadow-lg overflow-hidden">
          <div className="h-1.5 bg-gradient-to-r from-foundation via-keystone to-amber-500" />
          <CardContent className="p-5">
            <div className="flex justify-between items-start gap-4">
              <div>
                <p className="text-xs uppercase tracking-widest text-muted-foreground">
                  Next required action
                </p>
                <h2 className="font-serif text-2xl font-bold text-foundation mt-1">
                  {action?.label || "Day Complete"}
                </h2>
                <p className="text-sm text-muted-foreground mt-1">
                  {action?.detail || "All required punches are complete."}
                </p>
              </div>
              <div className="w-12 h-12 rounded-xl bg-keystone/10 flex items-center justify-center shrink-0">
                <ActionIcon className="w-6 h-6 text-keystone" />
              </div>
            </div>
            {attendance?.session?.window_expires_at &&
              nextEvent !== "browne_check_out" && (
                <p className="text-xs text-muted-foreground mt-4">
                  Punch window closes{" "}
                  {new Date(
                    attendance.session.window_expires_at,
                  ).toLocaleTimeString([], {
                    hour: "numeric",
                    minute: "2-digit",
                  })}
                  .
                </p>
              )}
          </CardContent>
        </Card>

        {clockStatus?.is_clocked_in && (
          <Card className="bg-foundation text-white border-0 shadow-md">
            <CardContent className="p-5 text-center">
              <p className="text-xs uppercase tracking-widest text-white/60">
                {isOnLunch ? "On lunch" : "Paid work time"}
              </p>
              <p className="font-mono text-5xl font-bold mt-2">
                {formatElapsed(elapsedTime)}
              </p>
            </CardContent>
          </Card>
        )}

        {!attendance?.session && (
          <Card className="bg-white border-0 shadow-md">
            <CardHeader className="pb-2">
              <CardTitle className="font-serif text-lg flex items-center gap-2 text-foundation">
                <MapPin className="w-5 h-5 text-keystone" /> Assigned Work Site
              </CardTitle>
            </CardHeader>
            <CardContent>
              <Select value={selectedSite} onValueChange={setSelectedSite}>
                <SelectTrigger
                  data-testid="site-select"
                  className="h-12 bg-horizon border-gray-200"
                >
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
                  {currentSite.address}
                </p>
              )}
            </CardContent>
          </Card>
        )}

        <Card className="bg-white border-0 shadow-md">
          <CardContent className="p-4 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Navigation className="w-5 h-5 text-keystone" />
              <span className="text-sm font-medium text-foundation">
                Precise location
              </span>
            </div>
            {location ? (
              <Badge
                variant="outline"
                className="text-green-700 border-green-200 bg-green-50"
              >
                <CheckCircle2 className="w-3 h-3 mr-1" /> ±
                {Math.round(location.accuracy)}m
              </Badge>
            ) : (
              <span className="text-xs text-vertex flex items-center gap-1">
                <AlertCircle className="w-4 h-4" />{" "}
                {locationError || "Acquiring..."}
              </span>
            )}
          </CardContent>
        </Card>

        {needsPhoto && (
          <Card className="bg-white border-0 shadow-md">
            <CardHeader className="pb-2">
              <CardTitle className="font-serif text-lg flex items-center gap-2 text-foundation">
                <Camera className="w-5 h-5 text-keystone" /> Photo Verification
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
                    className="w-full rounded-lg bg-foundation aspect-video"
                  />
                  <div className="flex gap-2">
                    <Button
                      onClick={capturePhoto}
                      className="flex-1 bg-keystone"
                    >
                      Capture
                    </Button>
                    <Button
                      onClick={stopCamera}
                      variant="outline"
                      className="flex-1"
                    >
                      Cancel
                    </Button>
                  </div>
                </div>
              ) : capturedPhoto ? (
                <div className="space-y-3">
                  <img
                    src={capturedPhoto}
                    alt="Verification"
                    className="w-full rounded-lg"
                  />
                  <Button
                    onClick={() => setCapturedPhoto(null)}
                    variant="outline"
                    className="w-full"
                  >
                    Retake
                  </Button>
                </div>
              ) : (
                <Button
                  onClick={startCamera}
                  variant="outline"
                  className="w-full h-24 border-dashed flex-col gap-2"
                >
                  <Camera className="w-7 h-7 text-keystone" /> Take photo
                </Button>
              )}
              <canvas ref={canvasRef} className="hidden" />
            </CardContent>
          </Card>
        )}

        {action && (
          <div className="pt-2">
            <Button
              data-testid={`${nextEvent}-btn`}
              onClick={handleAction}
              disabled={
                actionLoading || !location || (needsPhoto && !capturedPhoto)
              }
              className={`w-full h-16 text-lg font-bold rounded-xl shadow-lg ${
                action.color === "vertex"
                  ? "bg-vertex hover:bg-vertex/90"
                  : action.color === "foundation"
                    ? "bg-foundation hover:bg-foundation/90"
                    : "bg-keystone hover:bg-keystone/90"
              }`}
            >
              {actionLoading ? (
                <Loader2 className="w-6 h-6 animate-spin mr-2" />
              ) : (
                <ActionIcon className="w-6 h-6 mr-2" />
              )}
              {action.label}
            </Button>
            <p className="text-center text-xs text-muted-foreground mt-3">
              Location and time are captured when you tap this button.
            </p>
          </div>
        )}

        {attendance?.session?.events?.length > 0 && (
          <Card className="bg-white border-0 shadow-sm">
            <CardHeader className="pb-2">
              <CardTitle className="font-serif text-lg text-foundation">
                Today’s activity
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {attendance.session.events.map((event, index) => (
                <div
                  key={`${event.event_type}-${index}`}
                  className="flex items-center justify-between text-sm border-b last:border-0 pb-3 last:pb-0"
                >
                  <span className="text-foundation">
                    {ACTIONS[event.event_type]?.label || event.event_type}
                  </span>
                  <span className="font-mono text-muted-foreground">
                    {new Date(event.recorded_at).toLocaleTimeString([], {
                      hour: "numeric",
                      minute: "2-digit",
                    })}
                  </span>
                </div>
              ))}
            </CardContent>
          </Card>
        )}
      </div>
    </Layout>
  );
};

export default Dashboard;
