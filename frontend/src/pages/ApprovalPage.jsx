import { useState, useEffect } from "react";
import { useParams, useSearchParams } from "react-router-dom";
import axios from "axios";
import { toast } from "sonner";
import { format } from "date-fns";
import { API } from "../App";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { Textarea } from "../components/ui/textarea";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../components/ui/table";
import { 
  CheckCircle2, XCircle, Clock, MapPin, User, 
  Calendar, Loader2, FileText, Camera
} from "lucide-react";

const ApprovalPage = () => {
  const { timesheetId } = useParams();
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token");
  
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [notes, setNotes] = useState("");
  const [completed, setCompleted] = useState(false);

  useEffect(() => {
    const fetchTimesheet = async () => {
      try {
        const response = await axios.get(`${API}/timesheets/${timesheetId}`, {
          params: { token }
        });
        setData(response.data);
        
        if (response.data.timesheet?.status !== "submitted") {
          setCompleted(true);
        }
      } catch (error) {
        toast.error(error.response?.data?.detail || "Failed to load timesheet");
      } finally {
        setLoading(false);
      }
    };

    fetchTimesheet();
  }, [timesheetId, token]);

  const handleApproval = async (action) => {
    setProcessing(true);
    try {
      await axios.post(`${API}/timesheets/${timesheetId}/approve`, {
        timesheet_id: timesheetId,
        action,
        notes: notes || null
      }, {
        params: { token }
      });
      
      toast.success(`Timesheet ${action === "approve" ? "approved" : "rejected"}`);
      setCompleted(true);
      
      // Refresh data
      const response = await axios.get(`${API}/timesheets/${timesheetId}`, {
        params: { token }
      });
      setData(response.data);
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to process approval");
    } finally {
      setProcessing(false);
    }
  };

  const formatTime = (isoString) => {
    if (!isoString) return "-";
    return format(new Date(isoString), "HH:mm");
  };

  const formatDate = (isoString) => {
    if (!isoString) return "-";
    return format(new Date(isoString), "EEE, MMM d");
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-12 h-12 animate-spin text-primary mx-auto mb-4" />
          <p className="text-muted-foreground">Loading timesheet...</p>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center p-4">
        <Card className="max-w-md w-full bg-card border-border">
          <CardContent className="py-12 text-center">
            <XCircle className="w-16 h-16 mx-auto mb-4 text-destructive" />
            <h2 className="font-heading text-2xl font-bold mb-2">Timesheet Not Found</h2>
            <p className="text-muted-foreground">
              This timesheet may have been deleted or the link is invalid.
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  const { timesheet, entries, employee, site } = data;

  const getStatusBadge = (status) => {
    const config = {
      submitted: { variant: "outline", color: "text-secondary" },
      approved: { variant: "default", color: "text-success" },
      rejected: { variant: "destructive", color: "text-destructive" }
    };
    const c = config[status] || config.submitted;
    return (
      <Badge variant={c.variant} className={c.color}>
        {status.toUpperCase()}
      </Badge>
    );
  };

  return (
    <div className="min-h-screen bg-background noise-bg p-4">
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Header */}
        <div className="text-center py-6">
          <h1 className="font-heading text-4xl font-bold mb-2">SITE COMMANDER</h1>
          <p className="text-muted-foreground">Timesheet Approval</p>
        </div>

        {/* Status Banner */}
        {completed && (
          <Card className={`border-2 ${
            timesheet.status === "approved" ? "border-success bg-success/10" : 
            timesheet.status === "rejected" ? "border-destructive bg-destructive/10" : 
            "border-secondary bg-secondary/10"
          }`}>
            <CardContent className="py-4 text-center">
              {timesheet.status === "approved" ? (
                <div className="flex items-center justify-center gap-2 text-success">
                  <CheckCircle2 className="w-6 h-6" />
                  <span className="font-heading text-xl">Timesheet Approved</span>
                </div>
              ) : timesheet.status === "rejected" ? (
                <div className="flex items-center justify-center gap-2 text-destructive">
                  <XCircle className="w-6 h-6" />
                  <span className="font-heading text-xl">Timesheet Rejected</span>
                </div>
              ) : null}
              {timesheet.notes && (
                <p className="text-sm mt-2 text-muted-foreground">Note: {timesheet.notes}</p>
              )}
            </CardContent>
          </Card>
        )}

        {/* Employee Info */}
        <Card className="bg-card border-border">
          <CardContent className="p-6">
            <div className="flex flex-col sm:flex-row sm:items-center gap-4">
              <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center overflow-hidden">
                {employee?.picture ? (
                  <img src={employee.picture} alt="" className="w-full h-full object-cover" />
                ) : (
                  <User className="w-8 h-8 text-muted-foreground" />
                )}
              </div>
              
              <div className="flex-1">
                <h2 className="font-heading text-2xl font-bold">{employee?.name || "Unknown Employee"}</h2>
                <div className="flex flex-wrap gap-4 mt-2 text-sm text-muted-foreground">
                  <span className="flex items-center gap-1">
                    <MapPin className="w-4 h-4" />
                    {site?.name || "Unknown Site"}
                  </span>
                  <span className="flex items-center gap-1">
                    <Calendar className="w-4 h-4" />
                    {format(new Date(timesheet.week_start), "MMM d")} - {format(new Date(timesheet.week_end), "MMM d, yyyy")}
                  </span>
                </div>
              </div>
              
              <div className="text-right">
                <p className="font-mono text-4xl font-bold text-primary">{timesheet.total_hours?.toFixed(2)}h</p>
                <p className="text-sm text-muted-foreground">{entries?.length || 0} entries</p>
                <div className="mt-2">{getStatusBadge(timesheet.status)}</div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Entries Table */}
        <Card className="bg-card border-border">
          <CardHeader>
            <CardTitle className="font-heading text-xl flex items-center gap-2">
              <Clock className="w-5 h-5 text-primary" />
              Time Entries
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <Table className="data-table">
                <TableHeader>
                  <TableRow>
                    <TableHead>Date</TableHead>
                    <TableHead>Clock In</TableHead>
                    <TableHead>Clock Out</TableHead>
                    <TableHead>Lunch</TableHead>
                    <TableHead>Hours</TableHead>
                    <TableHead>Location</TableHead>
                    <TableHead>Photo</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {entries?.map((entry) => (
                    <TableRow key={entry.entry_id}>
                      <TableCell>{formatDate(entry.clock_in)}</TableCell>
                      <TableCell className="font-mono">{formatTime(entry.clock_in)}</TableCell>
                      <TableCell className="font-mono">{formatTime(entry.clock_out)}</TableCell>
                      <TableCell className="font-mono">
                        {entry.lunch_start && entry.lunch_end 
                          ? `${formatTime(entry.lunch_start)}-${formatTime(entry.lunch_end)}`
                          : "-"
                        }
                      </TableCell>
                      <TableCell className="font-mono font-semibold">
                        {entry.total_hours?.toFixed(2) || "-"}
                      </TableCell>
                      <TableCell>
                        {entry.location_verified ? (
                          <Badge variant="outline" className="text-success border-success">
                            <CheckCircle2 className="w-3 h-3 mr-1" />
                            Verified
                          </Badge>
                        ) : (
                          <Badge variant="outline" className="text-destructive border-destructive">
                            <XCircle className="w-3 h-3 mr-1" />
                            Off-site
                          </Badge>
                        )}
                      </TableCell>
                      <TableCell>
                        {entry.clock_in_photo ? (
                          <Badge variant="outline" className="text-secondary">
                            <Camera className="w-3 h-3 mr-1" />
                            Yes
                          </Badge>
                        ) : (
                          <span className="text-muted-foreground">-</span>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>

        {/* Approval Actions */}
        {!completed && timesheet.status === "submitted" && (
          <Card className="bg-card border-border">
            <CardHeader>
              <CardTitle className="font-heading text-xl flex items-center gap-2">
                <FileText className="w-5 h-5 text-primary" />
                Manager Review
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="text-sm text-muted-foreground">Notes (optional)</label>
                <Textarea
                  data-testid="approval-notes"
                  placeholder="Add any notes or corrections..."
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  className="mt-1 bg-background"
                />
              </div>
              
              <div className="flex gap-3">
                <Button
                  data-testid="approve-btn"
                  onClick={() => handleApproval("approve")}
                  disabled={processing}
                  className="flex-1 bg-success hover:bg-success/90"
                >
                  {processing ? (
                    <Loader2 className="w-4 h-4 animate-spin mr-2" />
                  ) : (
                    <CheckCircle2 className="w-4 h-4 mr-2" />
                  )}
                  Approve Timesheet
                </Button>
                
                <Button
                  data-testid="reject-btn"
                  variant="destructive"
                  onClick={() => handleApproval("reject")}
                  disabled={processing}
                  className="flex-1"
                >
                  {processing ? (
                    <Loader2 className="w-4 h-4 animate-spin mr-2" />
                  ) : (
                    <XCircle className="w-4 h-4 mr-2" />
                  )}
                  Reject Timesheet
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Footer */}
        <p className="text-center text-xs text-muted-foreground py-4">
          Site Commander • Workforce Time Tracking
        </p>
      </div>
    </div>
  );
};

export default ApprovalPage;
